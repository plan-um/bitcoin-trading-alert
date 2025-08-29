#!/usr/bin/env python3
"""
비트코인 매매 전략 알람 시스템
과열도 지표를 모니터링하고 단계별 청산 알람을 발송합니다.
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
from typing import Dict, Tuple
import os
from plyer import notification
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bitcoin_alert.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BitcoinIndicators:
    """비트코인 지표 계산 클래스"""
    
    def __init__(self):
        self.last_alert_level = 0
        self.indicators_weight = {
            'pi_cycle_top': 0.30,
            'nupl': 0.25,
            'rsi_weekly': 0.20,
            'google_trends': 0.15,
            'kimchi_premium': 0.10
        }
    
    def get_bitcoin_price(self) -> float:
        """현재 비트코인 가격 조회 (USD)"""
        try:
            response = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd')
            return response.json()['bitcoin']['usd']
        except Exception as e:
            logger.error(f"비트코인 가격 조회 실패: {e}")
            return 0
    
    def get_bitcoin_price_krw(self) -> float:
        """한국 비트코인 가격 조회 (KRW)"""
        try:
            # Bithumb API 사용
            response = requests.get('https://api.bithumb.com/public/ticker/BTC_KRW')
            data = response.json()
            if data['status'] == '0000':
                return float(data['data']['closing_price'])
        except Exception as e:
            logger.error(f"한국 비트코인 가격 조회 실패: {e}")
        return 0
    
    def calculate_rsi(self, prices: list, period: int = 14) -> float:
        """RSI 계산"""
        if len(prices) < period + 1:
            return 50  # 데이터 부족시 중립값 반환
        
        prices = np.array(prices)
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def get_weekly_rsi(self) -> float:
        """주간 RSI 조회"""
        try:
            # 90일 데이터로 주간 RSI 계산
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)
            
            url = f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart/range"
            params = {
                'vs_currency': 'usd',
                'from': int(start_date.timestamp()),
                'to': int(end_date.timestamp())
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            # 주간 데이터로 변환
            prices = [price[1] for price in data['prices']]
            weekly_prices = prices[::7]  # 7일마다 샘플링
            
            if len(weekly_prices) > 14:
                return self.calculate_rsi(weekly_prices, 14)
            
        except Exception as e:
            logger.error(f"주간 RSI 계산 실패: {e}")
        
        return 50  # 오류시 중립값 반환
    
    def check_pi_cycle_top(self) -> bool:
        """Pi Cycle Top 지표 확인
        111일 이동평균 * 2 > 350일 이동평균 체크
        """
        try:
            # 1년 데이터 가져오기
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            
            url = f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart/range"
            params = {
                'vs_currency': 'usd',
                'from': int(start_date.timestamp()),
                'to': int(end_date.timestamp())
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            prices = [price[1] for price in data['prices']]
            
            if len(prices) >= 350:
                ma_111 = np.mean(prices[-111:])
                ma_350 = np.mean(prices[-350:])
                
                # Pi Cycle Top 조건: 111일 MA * 2 > 350일 MA
                return (ma_111 * 2) > ma_350
            
        except Exception as e:
            logger.error(f"Pi Cycle Top 계산 실패: {e}")
        
        return False
    
    def calculate_nupl(self) -> float:
        """NUPL (Net Unrealized Profit/Loss) 계산
        실제 구현시에는 온체인 데이터 API 필요
        여기서는 시뮬레이션 값 사용
        """
        # 실제로는 Glassnode 등의 API 사용 필요
        # 데모용 시뮬레이션
        current_price = self.get_bitcoin_price()
        
        # 가격 기반 추정 (실제로는 온체인 데이터 필요)
        if current_price > 100000:
            return 0.8
        elif current_price > 80000:
            return 0.7
        elif current_price > 60000:
            return 0.6
        else:
            return 0.5
    
    def get_google_trends_score(self) -> float:
        """구글 트렌드 점수 조회
        pytrends 라이브러리 사용
        """
        try:
            from pytrends.request import TrendReq
            
            pytrends = TrendReq(hl='ko', tz=540)
            pytrends.build_payload(['Bitcoin'], timeframe='now 7-d')
            
            interest = pytrends.interest_over_time()
            if not interest.empty:
                recent_interest = interest['Bitcoin'].iloc[-1]
                # 100점 만점 기준으로 정규화
                return recent_interest / 100
            
        except Exception as e:
            logger.error(f"구글 트렌드 조회 실패: {e}")
        
        return 0.5  # 오류시 중간값 반환
    
    def calculate_kimchi_premium(self) -> float:
        """김치 프리미엄 계산"""
        try:
            usd_price = self.get_bitcoin_price()
            krw_price = self.get_bitcoin_price_krw()
            
            if usd_price > 0 and krw_price > 0:
                # USD to KRW 환율 (간단히 고정값 사용, 실제로는 API 조회 필요)
                usd_to_krw = 1350
                
                usd_price_in_krw = usd_price * usd_to_krw
                premium = ((krw_price - usd_price_in_krw) / usd_price_in_krw) * 100
                
                return premium
            
        except Exception as e:
            logger.error(f"김치 프리미엄 계산 실패: {e}")
        
        return 0
    
    def calculate_heat_score(self) -> Tuple[float, Dict[str, bool]]:
        """과열도 점수 계산"""
        indicators_status = {}
        heat_score = 0
        
        # 1. Pi Cycle Top (30%)
        pi_cycle = self.check_pi_cycle_top()
        indicators_status['pi_cycle_top'] = pi_cycle
        if pi_cycle:
            heat_score += self.indicators_weight['pi_cycle_top']
        
        # 2. NUPL > 0.75 (25%)
        nupl = self.calculate_nupl()
        nupl_triggered = nupl > 0.75
        indicators_status['nupl'] = nupl_triggered
        if nupl_triggered:
            heat_score += self.indicators_weight['nupl']
        
        # 3. RSI 주간 > 85 (20%)
        rsi = self.get_weekly_rsi()
        rsi_triggered = rsi > 85
        indicators_status['rsi_weekly'] = rsi_triggered
        if rsi_triggered:
            heat_score += self.indicators_weight['rsi_weekly']
        
        # 4. 구글 트렌드 급증 (15%)
        trends = self.get_google_trends_score()
        trends_triggered = trends > 0.8  # 80% 이상일 때 급증으로 판단
        indicators_status['google_trends'] = trends_triggered
        if trends_triggered:
            heat_score += self.indicators_weight['google_trends']
        
        # 5. 김치 프리미엄 > 10% (10%)
        kimchi = self.calculate_kimchi_premium()
        kimchi_triggered = kimchi > 10
        indicators_status['kimchi_premium'] = kimchi_triggered
        if kimchi_triggered:
            heat_score += self.indicators_weight['kimchi_premium']
        
        # 상세 정보 로깅
        logger.info(f"지표 상태: Pi Cycle={pi_cycle}, NUPL={nupl:.2f}, RSI={rsi:.2f}, Trends={trends:.2f}, Kimchi={kimchi:.2f}%")
        
        return heat_score * 100, indicators_status
    
    def get_action_level(self, heat_score: float) -> Tuple[int, str]:
        """과열도 점수에 따른 액션 레벨 결정"""
        if heat_score < 30:
            return 0, "홀드"
        elif heat_score < 50:
            return 1, "20% 청산"
        elif heat_score < 70:
            return 2, "누적 50% 청산"
        elif heat_score < 85:
            return 3, "누적 80% 청산"
        else:
            return 4, "완전 청산"
    
    def send_notification(self, title: str, message: str):
        """데스크톱 알림 발송"""
        try:
            notification.notify(
                title=title,
                message=message,
                app_icon=None,
                timeout=10
            )
            logger.info(f"알림 발송: {title} - {message}")
        except Exception as e:
            logger.error(f"알림 발송 실패: {e}")
    
    def check_and_alert(self):
        """지표 확인 및 알람 발송"""
        heat_score, indicators = self.calculate_heat_score()
        level, action = self.get_action_level(heat_score)
        
        # 현재 상태 출력
        logger.info(f"과열도 점수: {heat_score:.1f}%")
        logger.info(f"액션 레벨: {level} - {action}")
        
        # 레벨 변경시 알림
        if level != self.last_alert_level:
            if level > self.last_alert_level:
                title = f"⚠️ 비트코인 과열도 상승!"
                message = f"과열도: {heat_score:.1f}%\n권장 액션: {action}"
                
                # 트리거된 지표 표시
                triggered = [k for k, v in indicators.items() if v]
                if triggered:
                    message += f"\n발동 지표: {', '.join(triggered)}"
                
                self.send_notification(title, message)
            else:
                title = f"✅ 비트코인 과열도 하락"
                message = f"과열도: {heat_score:.1f}%\n현재 단계: {action}"
                self.send_notification(title, message)
            
            self.last_alert_level = level
        
        return heat_score, level, action
    
    def run_monitor(self, interval_minutes: int = 30):
        """모니터링 실행"""
        logger.info(f"비트코인 과열도 모니터링 시작 (체크 간격: {interval_minutes}분)")
        
        while True:
            try:
                heat_score, level, action = self.check_and_alert()
                
                # 상태 저장 (JSON 파일)
                status = {
                    'timestamp': datetime.now().isoformat(),
                    'heat_score': heat_score,
                    'level': level,
                    'action': action,
                    'bitcoin_price_usd': self.get_bitcoin_price(),
                    'bitcoin_price_krw': self.get_bitcoin_price_krw()
                }
                
                with open('bitcoin_status.json', 'w') as f:
                    json.dump(status, f, indent=2)
                
                # 대기
                time.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                logger.info("모니터링 종료")
                break
            except Exception as e:
                logger.error(f"모니터링 오류: {e}")
                time.sleep(60)  # 오류시 1분 후 재시도

def main():
    """메인 실행 함수"""
    monitor = BitcoinIndicators()
    
    # 체크 간격 설정 (분 단위)
    interval = int(os.getenv('CHECK_INTERVAL', 30))
    
    # 즉시 한 번 체크
    heat_score, level, action = monitor.check_and_alert()
    print(f"\n현재 과열도: {heat_score:.1f}%")
    print(f"권장 액션: {action}")
    print(f"\n{interval}분마다 자동 체크합니다...")
    
    # 지속적 모니터링
    monitor.run_monitor(interval)

if __name__ == "__main__":
    main()