#!/usr/bin/env python3
"""
비트코인 투자 전략 통합 시스템
- 과열도 모니터링 (매도 시그널)
- 축적도 모니터링 (매수 시그널)
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
from typing import Dict, Tuple, Optional
import os
from plyer import notification
import logging
from pytrends.request import TrendReq
import schedule

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bitcoin_strategy.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BitcoinStrategySystem:
    """비트코인 투자 전략 통합 시스템"""
    
    def __init__(self):
        # 과열도 지표 가중치
        self.heat_indicators_weight = {
            'pi_cycle_top': 0.30,
            'nupl': 0.25,
            'rsi_weekly': 0.20,
            'google_trends': 0.15,
            'kimchi_premium': 0.10
        }
        
        # 축적도 지표 가중치
        self.accumulation_indicators_weight = {
            'fear_greed': 0.40,  # Fear & Greed Index
            'exchange_balance': 0.35,  # 거래소 잔고
            'long_term_holder': 0.25  # 장기 보유자
        }
        
        self.last_heat_level = 0
        self.last_accumulation_level = 0
        
        # API 제한 관리
        self.last_api_call = {}
        self.api_limits = {
            'coingecko': 10,
            'google_trends': 60,
            'alternative_me': 10,  # Fear & Greed API
        }
        
        # 반감기 정보 (하드코딩)
        self.halvings = [
            datetime(2024, 4, 20),  # 4차 반감기 (예상)
            datetime(2028, 4, 20),  # 5차 반감기 (예상)
        ]
    
    def rate_limit(self, api_name: str):
        """API 호출 제한"""
        if api_name in self.last_api_call:
            elapsed = time.time() - self.last_api_call[api_name]
            wait_time = self.api_limits.get(api_name, 1) - elapsed
            if wait_time > 0:
                time.sleep(wait_time)
        self.last_api_call[api_name] = time.time()
    
    # ===== 공통 가격 조회 함수 =====
    
    def get_bitcoin_price_usd(self) -> float:
        """USD 가격 조회"""
        try:
            response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT')
            return float(response.json()['price'])
        except:
            try:
                self.rate_limit('coingecko')
                response = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd')
                return response.json()['bitcoin']['usd']
            except Exception as e:
                logger.error(f"USD 가격 조회 실패: {e}")
                return 0
    
    def get_bitcoin_price_krw(self) -> float:
        """KRW 가격 조회"""
        try:
            response = requests.get('https://api.bithumb.com/public/ticker/BTC_KRW')
            data = response.json()
            if data['status'] == '0000':
                return float(data['data']['closing_price'])
        except:
            try:
                response = requests.get('https://api.upbit.com/v1/ticker?markets=KRW-BTC')
                return response.json()[0]['trade_price']
            except Exception as e:
                logger.error(f"KRW 가격 조회 실패: {e}")
        return 0
    
    def get_exchange_rate(self) -> float:
        """USD/KRW 환율"""
        try:
            response = requests.get('https://quotation-api-cdn.dunamu.com/v1/forex/recent?codes=FRX.KRWUSD')
            return response.json()[0]['basePrice']
        except:
            return 1350
    
    def get_historical_prices(self, days: int) -> list:
        """과거 가격 데이터"""
        try:
            self.rate_limit('coingecko')
            url = f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
            params = {'vs_currency': 'usd', 'days': days, 'interval': 'daily'}
            response = requests.get(url, params=params)
            return [price[1] for price in response.json()['prices']]
        except Exception as e:
            logger.error(f"과거 가격 조회 실패: {e}")
            return []
    
    # ===== 과열도 지표 (매도) =====
    
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
        return 100 - (100 / (1 + rs))
    
    def get_weekly_rsi(self) -> float:
        """주간 RSI"""
        try:
            prices = self.get_historical_prices(100)
            if prices:
                weekly_prices = prices[::7]
                if len(weekly_prices) > 14:
                    return self.calculate_rsi(weekly_prices, 14)
        except Exception as e:
            logger.error(f"RSI 계산 실패: {e}")
        return 50
    
    def check_pi_cycle_top(self) -> bool:
        """Pi Cycle Top"""
        try:
            prices = self.get_historical_prices(365)
            if len(prices) >= 350:
                ma_111 = np.mean(prices[-111:])
                ma_350 = np.mean(prices[-350:])
                return (ma_111 * 2) > (ma_350 * 1.05)
        except Exception as e:
            logger.error(f"Pi Cycle Top 계산 실패: {e}")
        return False
    
    def estimate_nupl(self) -> float:
        """NUPL 추정"""
        try:
            current_price = self.get_bitcoin_price_usd()
            prices_365 = self.get_historical_prices(365)
            
            if prices_365 and current_price > 0:
                ma_200 = np.mean(prices_365[-200:]) if len(prices_365) >= 200 else np.mean(prices_365)
                mvrv_approx = current_price / ma_200
                nupl_estimate = (mvrv_approx - 1) / mvrv_approx if mvrv_approx > 1 else 0
                
                ath = max(prices_365) if prices_365 else current_price
                position_in_cycle = current_price / ath
                
                return min((nupl_estimate * 0.7) + (position_in_cycle * 0.3), 0.95)
        except Exception as e:
            logger.error(f"NUPL 추정 실패: {e}")
        return 0.5
    
    def get_google_trends_score(self) -> float:
        """구글 트렌드"""
        try:
            self.rate_limit('google_trends')
            pytrends = TrendReq(hl='ko', tz=540, timeout=(10,25))
            pytrends.build_payload(['Bitcoin'], timeframe='now 7-d')
            interest = pytrends.interest_over_time()
            
            if not interest.empty:
                recent = interest['Bitcoin'].iloc[-1]
                avg = interest['Bitcoin'].mean()
                surge_ratio = recent / avg if avg > 0 else 1
                return min((surge_ratio - 1) / 0.5, 1.0) if surge_ratio > 1 else 0
        except Exception as e:
            logger.error(f"Google Trends 조회 실패: {e}")
        return 0.3
    
    def calculate_kimchi_premium(self) -> float:
        """김치 프리미엄"""
        try:
            usd_price = self.get_bitcoin_price_usd()
            krw_price = self.get_bitcoin_price_krw()
            exchange_rate = self.get_exchange_rate()
            
            if all([usd_price > 0, krw_price > 0, exchange_rate > 0]):
                usd_in_krw = usd_price * exchange_rate
                return ((krw_price - usd_in_krw) / usd_in_krw) * 100
        except Exception as e:
            logger.error(f"김치 프리미엄 계산 실패: {e}")
        return 0
    
    # ===== 축적도 지표 (매수) =====
    
    def get_fear_greed_index(self) -> int:
        """Fear & Greed Index 조회"""
        try:
            self.rate_limit('alternative_me')
            response = requests.get('https://api.alternative.me/fng/')
            data = response.json()
            if 'data' in data and len(data['data']) > 0:
                value = int(data['data'][0]['value'])
                classification = data['data'][0]['value_classification']
                logger.info(f"Fear & Greed: {value} ({classification})")
                return value
        except Exception as e:
            logger.error(f"Fear & Greed 조회 실패: {e}")
        return 50  # 중립값
    
    def estimate_exchange_balance_trend(self) -> float:
        """거래소 BTC 잔고 추세 추정
        실제로는 Glassnode API 필요, 여기서는 가격 변동성으로 추정
        """
        try:
            prices = self.get_historical_prices(30)
            if len(prices) > 7:
                # 최근 7일 vs 이전 기간 거래량/변동성 비교
                recent_volatility = np.std(prices[-7:])
                prev_volatility = np.std(prices[-14:-7])
                
                # 변동성 감소 = 거래소 잔고 감소 추정
                if prev_volatility > 0:
                    trend = 1 - (recent_volatility / prev_volatility)
                    # -1 (증가) ~ 1 (감소)로 정규화
                    return max(min(trend, 1), -1)
        except Exception as e:
            logger.error(f"거래소 잔고 추세 추정 실패: {e}")
        return 0
    
    def estimate_long_term_holder_accumulation(self) -> float:
        """장기 보유자 축적 추정
        150일 이상 보유 코인의 비율 추정
        """
        try:
            prices = self.get_historical_prices(200)
            if len(prices) > 150:
                # 150일 전 가격 대비 현재 가격
                price_150d_ago = prices[-150]
                current_price = prices[-1]
                
                # 가격이 하락했지만 거래량이 적으면 장기 보유 증가로 추정
                price_change = (current_price - price_150d_ago) / price_150d_ago
                
                if price_change < 0:
                    # 하락장에서 축적 신호
                    return min(abs(price_change) * 2, 1)
                else:
                    # 상승장에서는 축적 감소
                    return max(1 - price_change, 0)
        except Exception as e:
            logger.error(f"장기 보유자 추정 실패: {e}")
        return 0.5
    
    def get_months_until_halving(self) -> Optional[int]:
        """다음 반감기까지 남은 개월 수"""
        now = datetime.now()
        for halving_date in self.halvings:
            if halving_date > now:
                months = (halving_date - now).days / 30
                return int(months)
        return None
    
    # ===== 점수 계산 =====
    
    def calculate_heat_score(self) -> Tuple[float, Dict]:
        """과열도 점수 (매도 신호)"""
        indicators = {}
        heat_score = 0
        details = {}
        
        # Pi Cycle Top
        pi_cycle = self.check_pi_cycle_top()
        indicators['pi_cycle_top'] = pi_cycle
        if pi_cycle:
            heat_score += self.heat_indicators_weight['pi_cycle_top']
        
        # NUPL
        nupl = self.estimate_nupl()
        nupl_triggered = nupl > 0.75
        indicators['nupl'] = nupl_triggered
        details['nupl_value'] = nupl
        if nupl_triggered:
            heat_score += self.heat_indicators_weight['nupl']
        
        # RSI
        rsi = self.get_weekly_rsi()
        rsi_triggered = rsi > 85
        indicators['rsi_weekly'] = rsi_triggered
        details['rsi_value'] = rsi
        if rsi_triggered:
            heat_score += self.heat_indicators_weight['rsi_weekly']
        
        # Google Trends
        trends = self.get_google_trends_score()
        trends_triggered = trends > 0.7
        indicators['google_trends'] = trends_triggered
        details['trends_value'] = trends
        if trends_triggered:
            heat_score += self.heat_indicators_weight['google_trends']
        
        # 김치 프리미엄
        kimchi = self.calculate_kimchi_premium()
        kimchi_triggered = kimchi > 10
        indicators['kimchi_premium'] = kimchi_triggered
        details['kimchi_value'] = kimchi
        if kimchi_triggered:
            heat_score += self.heat_indicators_weight['kimchi_premium']
        
        return heat_score * 100, indicators, details
    
    def calculate_accumulation_score(self) -> Tuple[float, Dict]:
        """축적도 점수 (매수 신호)"""
        indicators = {}
        accumulation_score = 0
        details = {}
        
        # Fear & Greed Index < 30
        fear_greed = self.get_fear_greed_index()
        fear_triggered = fear_greed < 30
        indicators['fear_greed'] = fear_triggered
        details['fear_greed_value'] = fear_greed
        if fear_triggered:
            accumulation_score += self.accumulation_indicators_weight['fear_greed']
        
        # 거래소 잔고 감소
        exchange_trend = self.estimate_exchange_balance_trend()
        exchange_triggered = exchange_trend > 0.3  # 30% 이상 감소 추세
        indicators['exchange_balance'] = exchange_triggered
        details['exchange_trend'] = exchange_trend
        if exchange_triggered:
            accumulation_score += self.accumulation_indicators_weight['exchange_balance']
        
        # 장기 보유자 축적
        lth_accumulation = self.estimate_long_term_holder_accumulation()
        lth_triggered = lth_accumulation > 0.6
        indicators['long_term_holder'] = lth_triggered
        details['lth_value'] = lth_accumulation
        if lth_triggered:
            accumulation_score += self.accumulation_indicators_weight['long_term_holder']
        
        # 반감기 타이밍 보너스
        months_to_halving = self.get_months_until_halving()
        details['months_to_halving'] = months_to_halving
        if months_to_halving and 6 <= months_to_halving <= 18:
            accumulation_score *= 1.2  # 20% 보너스
            indicators['halving_window'] = True
        else:
            indicators['halving_window'] = False
        
        return min(accumulation_score * 100, 100), indicators, details
    
    def calculate_dca_amount(self, base_amount: float, fear_greed: int) -> float:
        """DCA 금액 계산"""
        if fear_greed < 30:
            adjustment = (30 - fear_greed) / 100
            return base_amount * (1 + adjustment)
        return base_amount
    
    # ===== 액션 레벨 =====
    
    def get_heat_action(self, heat_score: float) -> Tuple[int, str]:
        """과열도 액션"""
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
    
    def get_accumulation_action(self, acc_score: float, fear_greed: int) -> Tuple[int, str]:
        """축적도 액션"""
        base_amount = 1000  # 기본 DCA 금액 (달러)
        
        if acc_score < 30:
            return 0, "대기"
        elif acc_score < 50:
            dca = self.calculate_dca_amount(base_amount, fear_greed)
            return 1, f"소량 매수 (DCA ${dca:.0f}/주)"
        elif acc_score < 70:
            dca = self.calculate_dca_amount(base_amount * 1.5, fear_greed)
            return 2, f"적극 매수 (DCA ${dca:.0f}/주)"
        else:
            dca = self.calculate_dca_amount(base_amount * 2, fear_greed)
            return 3, f"최대 매수 (DCA ${dca:.0f}/주)"
    
    # ===== 알림 시스템 =====
    
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
        """전체 체크 및 알람"""
        # 가격 정보
        btc_usd = self.get_bitcoin_price_usd()
        btc_krw = self.get_bitcoin_price_krw()
        
        # 과열도 계산
        heat_score, heat_indicators, heat_details = self.calculate_heat_score()
        heat_level, heat_action = self.get_heat_action(heat_score)
        
        # 축적도 계산
        acc_score, acc_indicators, acc_details = self.calculate_accumulation_score()
        fear_greed = acc_details.get('fear_greed_value', 50)
        acc_level, acc_action = self.get_accumulation_action(acc_score, fear_greed)
        
        # 콘솔 출력
        print("\n" + "="*70)
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"💵 BTC/USD: ${btc_usd:,.0f} | 🇰🇷 BTC/KRW: ₩{btc_krw:,.0f}")
        
        if acc_details.get('months_to_halving'):
            print(f"⏰ 다음 반감기까지: {acc_details['months_to_halving']}개월")
        
        print("-"*70)
        print("🔥 과열도 (매도 신호)")
        print(f"   점수: {heat_score:.1f}% → {heat_action}")
        print(f"   • Pi Cycle: {'✅' if heat_indicators['pi_cycle_top'] else '❌'}")
        print(f"   • NUPL: {heat_details['nupl_value']:.2f} {'✅' if heat_indicators['nupl'] else '❌'}")
        print(f"   • RSI: {heat_details['rsi_value']:.1f} {'✅' if heat_indicators['rsi_weekly'] else '❌'}")
        print(f"   • Trends: {heat_details['trends_value']*100:.0f}% {'✅' if heat_indicators['google_trends'] else '❌'}")
        print(f"   • 김프: {heat_details['kimchi_value']:.1f}% {'✅' if heat_indicators['kimchi_premium'] else '❌'}")
        
        print("-"*70)
        print("💎 축적도 (매수 신호)")
        print(f"   점수: {acc_score:.1f}% → {acc_action}")
        print(f"   • Fear&Greed: {fear_greed} {'✅' if acc_indicators['fear_greed'] else '❌'}")
        print(f"   • 거래소 잔고: {acc_details['exchange_trend']:.1%} {'✅' if acc_indicators['exchange_balance'] else '❌'}")
        print(f"   • 장기 보유자: {acc_details['lth_value']:.1%} {'✅' if acc_indicators['long_term_holder'] else '❌'}")
        print(f"   • 반감기 구간: {'✅' if acc_indicators['halving_window'] else '❌'}")
        print("="*70)
        
        # 과열도 레벨 변경 알림
        if heat_level != self.last_heat_level:
            if heat_level > self.last_heat_level:
                title = f"🔥 과열도 레벨 {heat_level}"
                message = f"점수: {heat_score:.0f}%\n{heat_action}"
            else:
                title = f"❄️ 과열도 하락"
                message = f"점수: {heat_score:.0f}%\n{heat_action}"
            self.send_notification(title, message)
            self.last_heat_level = heat_level
        
        # 축적도 레벨 변경 알림
        if acc_level != self.last_accumulation_level:
            if acc_level > self.last_accumulation_level:
                title = f"💎 축적 기회 레벨 {acc_level}"
                message = f"점수: {acc_score:.0f}%\n{acc_action}"
            else:
                title = f"📉 축적 신호 약화"
                message = f"점수: {acc_score:.0f}%\n{acc_action}"
            self.send_notification(title, message)
            self.last_accumulation_level = acc_level
        
        # 상태 저장
        status = {
            'timestamp': datetime.now().isoformat(),
            'btc_usd': btc_usd,
            'btc_krw': btc_krw,
            'heat': {
                'score': heat_score,
                'level': heat_level,
                'action': heat_action,
                'indicators': heat_indicators,
                'details': heat_details
            },
            'accumulation': {
                'score': acc_score,
                'level': acc_level,
                'action': acc_action,
                'indicators': acc_indicators,
                'details': acc_details
            }
        }
        
        with open('bitcoin_strategy_status.json', 'w', encoding='utf-8') as f:
            json.dump(status, f, indent=2, ensure_ascii=False)
        
        return status

def main():
    """메인 실행"""
    print("🚀 비트코인 투자 전략 시스템 시작")
    print("="*70)
    print("📊 과열도: 매도 시점 판단")
    print("💎 축적도: 매수 시점 판단")
    print("="*70)
    
    system = BitcoinStrategySystem()
    
    # 초기 체크
    system.check_and_alert()
    
    # 정기 체크 스케줄
    schedule.every(30).minutes.do(system.check_and_alert)
    
    print("\n⏰ 30분마다 자동 체크합니다...")
    print("종료: Ctrl+C")
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)
        except KeyboardInterrupt:
            print("\n👋 시스템 종료")
            break
        except Exception as e:
            logger.error(f"오류 발생: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()