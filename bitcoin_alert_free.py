#!/usr/bin/env python3
"""
비트코인 매매 전략 알람 시스템 - 무료 API 버전
완전 무료 API만 사용하여 구현
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
from pytrends.request import TrendReq
import schedule

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bitcoin_alert.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FreebitcoinIndicators:
    """무료 API만 사용하는 비트코인 지표 모니터링"""
    
    def __init__(self):
        self.last_alert_level = 0
        self.indicators_weight = {
            'pi_cycle_top': 0.30,
            'nupl': 0.25,
            'rsi_weekly': 0.20,
            'google_trends': 0.15,
            'kimchi_premium': 0.10
        }
        
        # API 제한 관리
        self.last_api_call = {}
        self.api_limits = {
            'coingecko': 10,  # 10초에 1번
            'google_trends': 60,  # 1분에 1번
            'bithumb': 1,  # 1초에 1번
        }
    
    def rate_limit(self, api_name: str):
        """API 호출 제한 관리"""
        if api_name in self.last_api_call:
            elapsed = time.time() - self.last_api_call[api_name]
            wait_time = self.api_limits.get(api_name, 1) - elapsed
            if wait_time > 0:
                time.sleep(wait_time)
        self.last_api_call[api_name] = time.time()
    
    def get_bitcoin_price_usd(self) -> float:
        """Binance API로 USD 가격 조회 (무료, 제한 넉넉)"""
        try:
            response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT')
            return float(response.json()['price'])
        except:
            # 백업: CoinGecko
            try:
                self.rate_limit('coingecko')
                response = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd')
                return response.json()['bitcoin']['usd']
            except Exception as e:
                logger.error(f"USD 가격 조회 실패: {e}")
                return 0
    
    def get_bitcoin_price_krw(self) -> float:
        """Bithumb API로 KRW 가격 조회 (무료)"""
        try:
            self.rate_limit('bithumb')
            response = requests.get('https://api.bithumb.com/public/ticker/BTC_KRW')
            data = response.json()
            if data['status'] == '0000':
                return float(data['data']['closing_price'])
        except:
            # 백업: Upbit API
            try:
                response = requests.get('https://api.upbit.com/v1/ticker?markets=KRW-BTC')
                return response.json()[0]['trade_price']
            except Exception as e:
                logger.error(f"KRW 가격 조회 실패: {e}")
        return 0
    
    def get_exchange_rate(self) -> float:
        """USD/KRW 환율 조회"""
        try:
            # 한국은행 API (무료, 키 필요없음)
            response = requests.get('https://quotation-api-cdn.dunamu.com/v1/forex/recent?codes=FRX.KRWUSD')
            data = response.json()
            return data[0]['basePrice']
        except:
            # 고정 환율 사용
            return 1350
    
    def get_historical_prices(self, days: int) -> list:
        """과거 가격 데이터 조회 (CoinGecko 무료)"""
        try:
            self.rate_limit('coingecko')
            url = f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': days,
                'interval': 'daily'
            }
            response = requests.get(url, params=params)
            data = response.json()
            return [price[1] for price in data['prices']]
        except Exception as e:
            logger.error(f"과거 가격 조회 실패: {e}")
            return []
    
    def calculate_rsi(self, prices: list, period: int = 14) -> float:
        """RSI 계산"""
        if len(prices) < period + 1:
            return 50
        
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
        """주간 RSI 계산 (무료)"""
        try:
            prices = self.get_historical_prices(100)
            if prices:
                # 주간 캔들로 변환 (7일마다 샘플링)
                weekly_prices = prices[::7]
                if len(weekly_prices) > 14:
                    return self.calculate_rsi(weekly_prices, 14)
        except Exception as e:
            logger.error(f"RSI 계산 실패: {e}")
        return 50
    
    def check_pi_cycle_top(self) -> bool:
        """Pi Cycle Top 지표 (무료)"""
        try:
            prices = self.get_historical_prices(365)
            
            if len(prices) >= 350:
                ma_111 = np.mean(prices[-111:])
                ma_350 = np.mean(prices[-350:])
                
                # Pi Cycle Top: 111일 MA * 2 > 350일 MA * 1.05 (약간의 버퍼)
                is_triggered = (ma_111 * 2) > (ma_350 * 1.05)
                logger.info(f"Pi Cycle: MA111*2={ma_111*2:.0f}, MA350={ma_350:.0f}, Triggered={is_triggered}")
                return is_triggered
                
        except Exception as e:
            logger.error(f"Pi Cycle Top 계산 실패: {e}")
        return False
    
    def estimate_nupl(self) -> float:
        """NUPL 추정 (무료 대안)
        실제 NUPL 대신 가격 기반 추정 + MVRV 근사값 사용
        """
        try:
            current_price = self.get_bitcoin_price_usd()
            prices_365 = self.get_historical_prices(365)
            
            if prices_365 and current_price > 0:
                # 200일 이동평균을 실현가격의 프록시로 사용
                ma_200 = np.mean(prices_365[-200:]) if len(prices_365) >= 200 else np.mean(prices_365)
                
                # MVRV 근사값 = 현재가격 / 200일 MA
                mvrv_approx = current_price / ma_200
                
                # NUPL 추정 (MVRV를 NUPL로 변환)
                # MVRV 1.0 = NUPL 0, MVRV 2.0 = NUPL 0.5, MVRV 3.0 = NUPL 0.67
                nupl_estimate = (mvrv_approx - 1) / mvrv_approx if mvrv_approx > 1 else 0
                
                # 추가 보정: 역사적 고점 대비 현재 위치
                ath = max(prices_365) if prices_365 else current_price
                position_in_cycle = current_price / ath
                
                # 최종 NUPL 추정값 (두 지표의 가중평균)
                nupl_final = (nupl_estimate * 0.7) + (position_in_cycle * 0.3)
                
                logger.info(f"NUPL 추정: MVRV={mvrv_approx:.2f}, Position={position_in_cycle:.2f}, NUPL={nupl_final:.2f}")
                return min(nupl_final, 0.95)  # 최대값 제한
                
        except Exception as e:
            logger.error(f"NUPL 추정 실패: {e}")
        return 0.5
    
    def get_google_trends_score(self) -> float:
        """구글 트렌드 점수 (무료, 제한있음)"""
        try:
            self.rate_limit('google_trends')
            
            pytrends = TrendReq(hl='ko', tz=540, timeout=(10,25))
            
            # 최근 7일 데이터
            pytrends.build_payload(['Bitcoin'], timeframe='now 7-d')
            interest = pytrends.interest_over_time()
            
            if not interest.empty:
                # 최근 값과 평균 비교
                recent = interest['Bitcoin'].iloc[-1]
                avg = interest['Bitcoin'].mean()
                
                # 급증 판단: 평균 대비 상승률
                surge_ratio = recent / avg if avg > 0 else 1
                
                # 0-1 사이로 정규화 (1.5배 이상이면 최대값)
                score = min((surge_ratio - 1) / 0.5, 1.0) if surge_ratio > 1 else 0
                
                logger.info(f"Google Trends: Recent={recent}, Avg={avg:.1f}, Score={score:.2f}")
                return score
                
        except Exception as e:
            logger.error(f"Google Trends 조회 실패: {e}")
        return 0.3  # 기본값
    
    def calculate_kimchi_premium(self) -> float:
        """김치 프리미엄 계산 (무료)"""
        try:
            usd_price = self.get_bitcoin_price_usd()
            krw_price = self.get_bitcoin_price_krw()
            exchange_rate = self.get_exchange_rate()
            
            if all([usd_price > 0, krw_price > 0, exchange_rate > 0]):
                usd_in_krw = usd_price * exchange_rate
                premium = ((krw_price - usd_in_krw) / usd_in_krw) * 100
                
                logger.info(f"김치 프리미엄: {premium:.2f}% (KRW: {krw_price:,.0f}, USD: ${usd_price:,.0f})")
                return premium
                
        except Exception as e:
            logger.error(f"김치 프리미엄 계산 실패: {e}")
        return 0
    
    def calculate_heat_score(self) -> Tuple[float, Dict]:
        """과열도 점수 계산"""
        indicators_status = {}
        heat_score = 0
        details = {}
        
        logger.info("="*50)
        logger.info("지표 계산 시작...")
        
        # 1. Pi Cycle Top (30%)
        pi_cycle = self.check_pi_cycle_top()
        indicators_status['pi_cycle_top'] = pi_cycle
        if pi_cycle:
            heat_score += self.indicators_weight['pi_cycle_top']
        
        # 2. NUPL > 0.75 (25%)
        nupl = self.estimate_nupl()
        nupl_triggered = nupl > 0.75
        indicators_status['nupl'] = nupl_triggered
        details['nupl_value'] = nupl
        if nupl_triggered:
            heat_score += self.indicators_weight['nupl']
        
        # 3. RSI 주간 > 85 (20%)
        rsi = self.get_weekly_rsi()
        rsi_triggered = rsi > 85
        indicators_status['rsi_weekly'] = rsi_triggered
        details['rsi_value'] = rsi
        if rsi_triggered:
            heat_score += self.indicators_weight['rsi_weekly']
        
        # 4. 구글 트렌드 급증 (15%)
        trends = self.get_google_trends_score()
        trends_triggered = trends > 0.7  # 70% 이상
        indicators_status['google_trends'] = trends_triggered
        details['trends_value'] = trends
        if trends_triggered:
            heat_score += self.indicators_weight['google_trends']
        
        # 5. 김치 프리미엄 > 10% (10%)
        kimchi = self.calculate_kimchi_premium()
        kimchi_triggered = kimchi > 10
        indicators_status['kimchi_premium'] = kimchi_triggered
        details['kimchi_value'] = kimchi
        if kimchi_triggered:
            heat_score += self.indicators_weight['kimchi_premium']
        
        logger.info("="*50)
        
        return heat_score * 100, indicators_status, details
    
    def get_action_level(self, heat_score: float) -> Tuple[int, str]:
        """과열도에 따른 액션"""
        if heat_score < 30:
            return 0, "홀드"
        elif heat_score < 50:
            return 1, "20% 청산 권장"
        elif heat_score < 70:
            return 2, "누적 50% 청산 권장"
        elif heat_score < 85:
            return 3, "누적 80% 청산 권장"
        else:
            return 4, "완전 청산 권장"
    
    def send_notification(self, title: str, message: str):
        """알림 발송"""
        try:
            notification.notify(
                title=title,
                message=message,
                app_icon=None,
                timeout=10
            )
            logger.info(f"📢 알림: {title}")
        except Exception as e:
            logger.error(f"알림 발송 실패: {e}")
    
    def check_and_alert(self):
        """지표 확인 및 알람"""
        heat_score, indicators, details = self.calculate_heat_score()
        level, action = self.get_action_level(heat_score)
        
        # 현재 가격
        btc_usd = self.get_bitcoin_price_usd()
        btc_krw = self.get_bitcoin_price_krw()
        
        # 상태 출력
        print("\n" + "="*60)
        print(f"🔥 과열도 점수: {heat_score:.1f}%")
        print(f"💵 BTC/USD: ${btc_usd:,.0f}")
        print(f"🇰🇷 BTC/KRW: ₩{btc_krw:,.0f}")
        print(f"📊 권장 액션: {action}")
        print("-"*60)
        print("지표 상세:")
        print(f"  • Pi Cycle Top: {'✅' if indicators['pi_cycle_top'] else '❌'}")
        print(f"  • NUPL: {details['nupl_value']:.2f} {'✅' if indicators['nupl'] else '❌'} (>0.75)")
        print(f"  • RSI (주간): {details['rsi_value']:.1f} {'✅' if indicators['rsi_weekly'] else '❌'} (>85)")
        print(f"  • Google Trends: {details['trends_value']*100:.0f}% {'✅' if indicators['google_trends'] else '❌'}")
        print(f"  • 김치 프리미엄: {details['kimchi_value']:.1f}% {'✅' if indicators['kimchi_premium'] else '❌'} (>10%)")
        print("="*60)
        
        # 레벨 변경시 알림
        if level != self.last_alert_level:
            if level > self.last_alert_level:
                title = f"⚠️ 과열도 레벨 {level} 도달!"
                message = f"점수: {heat_score:.0f}%\n{action}\nBTC: ${btc_usd:,.0f}"
            else:
                title = f"✅ 과열도 하락"
                message = f"점수: {heat_score:.0f}%\n현재: {action}"
            
            self.send_notification(title, message)
            self.last_alert_level = level
        
        # 상태 저장
        status = {
            'timestamp': datetime.now().isoformat(),
            'heat_score': heat_score,
            'level': level,
            'action': action,
            'btc_usd': btc_usd,
            'btc_krw': btc_krw,
            'indicators': indicators,
            'details': details
        }
        
        with open('bitcoin_status.json', 'w', encoding='utf-8') as f:
            json.dump(status, f, indent=2, ensure_ascii=False)
        
        return heat_score, level, action

def main():
    """메인 실행"""
    print("🚀 비트코인 과열도 모니터링 시작 (무료 API 버전)")
    print("="*60)
    
    monitor = FreebitcoinIndicators()
    
    # 초기 체크
    monitor.check_and_alert()
    
    # 정기 체크 스케줄 (30분마다)
    schedule.every(30).minutes.do(monitor.check_and_alert)
    
    print("\n⏰ 30분마다 자동 체크합니다...")
    print("종료: Ctrl+C")
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)
        except KeyboardInterrupt:
            print("\n👋 모니터링 종료")
            break
        except Exception as e:
            logger.error(f"오류 발생: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()