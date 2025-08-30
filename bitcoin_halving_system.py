#!/usr/bin/env python3
"""
비트코인 투자 전략 통합 시스템 - 반감기 사이클 포함
- 반감기 사이클 (30%)
- 과열도 모니터링 (나머지 70% 중 매도 지표)
- 축적도 모니터링 (나머지 70% 중 매수 지표)
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

class BitcoinHalvingStrategy:
    """반감기 사이클 기반 비트코인 투자 전략"""
    
    def __init__(self):
        # 반감기 정보 (과거 및 미래)
        self.halvings = [
            {'date': datetime(2012, 11, 28), 'number': 1},
            {'date': datetime(2016, 7, 9), 'number': 2},
            {'date': datetime(2020, 5, 11), 'number': 3},
            {'date': datetime(2024, 4, 20), 'number': 4},  # 4차 반감기
            {'date': datetime(2028, 4, 20), 'number': 5},  # 예상 5차 반감기
        ]
        
        # 반감기 사이클 지표 (30% 비중)
        self.halving_weight = 0.30
        
        # 과열도 지표 가중치 (전체 70% 중 비율 조정)
        self.heat_indicators_weight = {
            'pi_cycle_top': 0.21,      # 30% -> 21% (0.3 * 0.7)
            'nupl': 0.175,              # 25% -> 17.5%
            'rsi_weekly': 0.14,         # 20% -> 14%
            'google_trends': 0.105,     # 15% -> 10.5%
            'kimchi_premium': 0.07      # 10% -> 7%
        }
        
        # 축적도 지표 가중치 (전체 70% 중 비율 조정)
        self.accumulation_indicators_weight = {
            'fear_greed': 0.28,         # 40% -> 28% (0.4 * 0.7)
            'exchange_balance': 0.245,  # 35% -> 24.5%
            'long_term_holder': 0.175   # 25% -> 17.5%
        }
        
        self.last_heat_level = 0
        self.last_accumulation_level = 0
        self.last_halving_phase = ""
        
        # API 제한 관리
        self.last_api_call = {}
        self.api_limits = {
            'coingecko': 10,
            'google_trends': 60,
            'alternative_me': 10,
        }
    
    def get_current_halving_cycle(self) -> Dict:
        """현재 반감기 사이클 정보 계산"""
        now = datetime.now()
        
        # 현재 반감기 찾기
        current_halving = None
        next_halving = None
        
        for i, halving in enumerate(self.halvings):
            if halving['date'] <= now:
                current_halving = halving
                if i + 1 < len(self.halvings):
                    next_halving = self.halvings[i + 1]
            else:
                if next_halving is None:
                    next_halving = halving
                break
        
        if not current_halving:
            return {
                'phase': 'pre-halving',
                'current_halving': None,
                'months_since_halving': 0,
                'months_to_next_halving': (self.halvings[0]['date'] - now).days / 30,
                'cycle_position': 0,
                'recommendation': 'accumulation'
            }
        
        # 현재 반감기 이후 경과 개월
        months_since = (now - current_halving['date']).days / 30
        
        # 다음 반감기까지 남은 개월
        months_to_next = 0
        if next_halving:
            months_to_next = (next_halving['date'] - now).days / 30
        
        # 사이클 위치 계산 (0-100%)
        total_cycle_months = 48  # 4년 주기
        cycle_position = (months_since / total_cycle_months) * 100
        
        # 반감기 사이클 국면 판단
        phase = ""
        recommendation = ""
        phase_score = 0  # 0-100 점수
        
        if months_since < 0:  # 반감기 전
            if months_to_next <= 12:
                phase = "accumulation"
                recommendation = "적극 매수 (DCA)"
                phase_score = 80  # 매수 신호
            else:
                phase = "pre-accumulation"
                recommendation = "준비 단계"
                phase_score = 40
        elif months_since <= 6:
            phase = "early-bull"
            recommendation = "보유 유지"
            phase_score = 20  # 중립
        elif months_since <= 12:
            phase = "mid-bull"
            recommendation = "보유 유지, 추가 매수 중단"
            phase_score = 10  # 매수 중단
        elif months_since <= 18:
            phase = "late-bull"
            recommendation = "단계적 매도 시작"
            phase_score = -60  # 매도 신호
        elif months_since <= 24:
            phase = "distribution"
            recommendation = "적극 매도"
            phase_score = -80  # 강한 매도 신호
        elif months_since <= 36:
            phase = "bear-market"
            recommendation = "현금 보유"
            phase_score = -40  # 관망
        else:
            phase = "late-bear"
            recommendation = "매수 준비"
            phase_score = 60  # 매수 준비
        
        return {
            'phase': phase,
            'current_halving': current_halving,
            'next_halving': next_halving,
            'months_since_halving': months_since,
            'months_to_next_halving': months_to_next,
            'cycle_position': cycle_position,
            'recommendation': recommendation,
            'phase_score': phase_score,
            'halving_number': current_halving['number'] if current_halving else 0
        }
    
    def calculate_halving_signal(self) -> Tuple[float, str]:
        """반감기 사이클 기반 매매 신호 (30% 비중)
        Returns: (score, action) - score는 -100 ~ 100
        """
        cycle_info = self.get_current_halving_cycle()
        phase_score = cycle_info['phase_score']
        
        # 반감기 사이클 점수를 0-100 스케일로 변환
        # phase_score가 음수면 매도 신호, 양수면 매수 신호
        if phase_score < 0:
            # 매도 신호: 과열도에 기여
            heat_contribution = abs(phase_score)  # 0-100
            acc_contribution = 0
        else:
            # 매수 신호: 축적도에 기여
            heat_contribution = 0
            acc_contribution = phase_score  # 0-100
        
        return {
            'heat_contribution': heat_contribution * self.halving_weight,
            'acc_contribution': acc_contribution * self.halving_weight,
            'cycle_info': cycle_info
        }
    
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
        return 50
    
    def estimate_exchange_balance_trend(self) -> float:
        """거래소 BTC 잔고 추세 추정"""
        try:
            prices = self.get_historical_prices(30)
            if len(prices) > 7:
                recent_volatility = np.std(prices[-7:])
                prev_volatility = np.std(prices[-14:-7])
                
                if prev_volatility > 0:
                    trend = 1 - (recent_volatility / prev_volatility)
                    return max(min(trend, 1), -1)
        except Exception as e:
            logger.error(f"거래소 잔고 추세 추정 실패: {e}")
        return 0
    
    def estimate_long_term_holder_accumulation(self) -> float:
        """장기 보유자 축적 추정"""
        try:
            prices = self.get_historical_prices(200)
            if len(prices) > 150:
                price_150d_ago = prices[-150]
                current_price = prices[-1]
                
                price_change = (current_price - price_150d_ago) / price_150d_ago
                
                if price_change < 0:
                    return min(abs(price_change) * 2, 1)
                else:
                    return max(1 - price_change, 0)
        except Exception as e:
            logger.error(f"장기 보유자 추정 실패: {e}")
        return 0.5
    
    def get_months_until_halving(self) -> Optional[int]:
        """다음 반감기까지 남은 개월 수"""
        cycle_info = self.get_current_halving_cycle()
        return int(cycle_info['months_to_next_halving'])
    
    def get_months_since_halving(self) -> int:
        """현재 반감기 이후 경과 개월 수"""
        cycle_info = self.get_current_halving_cycle()
        return int(cycle_info['months_since_halving'])
    
    def get_cycle_phase(self, months_since: int) -> str:
        """사이클 국면 판단"""
        if months_since <= 6:
            return 'early-bull'
        elif months_since <= 12:
            return 'mid-bull'
        elif months_since <= 18:
            return 'late-bull'
        elif months_since <= 24:
            return 'distribution'
        elif months_since <= 36:
            return 'bear'
        else:
            return 'accumulation'
    
    def calculate_cycle_score(self, months_since: int, phase: str) -> float:
        """사이클 점수 계산 (0-1)"""
        if phase in ['late-bull', 'distribution']:
            # 매도 신호 강도 (12-24개월)
            if months_since <= 18:
                return 0.6 + (months_since - 12) / 6 * 0.4  # 0.6 -> 1.0
            else:
                return max(0.5, 1.0 - (months_since - 18) / 6 * 0.5)  # 1.0 -> 0.5
        elif phase in ['accumulation', 'bear']:
            # 중립/관망
            return 0.3
        else:
            # early-bull, mid-bull: 보유
            return 0.1
    
    def get_cycle_recommendation(self, phase: str, months_since: int) -> str:
        """사이클 기반 권고사항"""
        if phase == 'accumulation':
            return '축적 국면: 적극적인 분할 매수 권장 (DCA)'
        elif phase == 'early-bull':
            return '강세장 초기: 보유 유지, 추가 매수 가능'
        elif phase == 'mid-bull':
            return '강세장 중기: 보유 유지, 추가 매수 중단'
        elif phase == 'late-bull':
            return '강세장 정점 구간: 단계적 매도 시작 (매월 10-20%)'
        elif phase == 'distribution':
            return '분산 국면: 적극적 매도 권장 (남은 물량 청산)'
        elif phase == 'bear':
            return '약세장: 현금 보유, 다음 축적 국면까지 대기'
        else:
            return '시장 상황 관찰 필요'
    
    def analyze_halving_cycle(self) -> Dict:
        """반감기 사이클 분석 - 대시보드용"""
        months_since = self.get_months_since_halving()
        phase = self.get_cycle_phase(months_since)
        cycle_score = self.calculate_cycle_score(months_since, phase)
        recommendation = self.get_cycle_recommendation(phase, months_since)
        
        return {
            'phase': phase,
            'months_since': months_since,
            'cycle_score': cycle_score,
            'recommendation': recommendation
        }
    
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
            return 3, f"최대 매수 (DCA ${dca:.0f}/주, 2x 금액)"
    
    def calculate_dca_amount(self, base_amount: float, fear_greed: int) -> float:
        """Fear & Greed 지수에 따른 DCA 금액 조정"""
        if fear_greed < 20:
            return base_amount * 1.5
        elif fear_greed < 40:
            return base_amount * 1.2
        elif fear_greed > 60:
            return base_amount * 0.8
        return base_amount
    
    # ===== 통합 점수 계산 =====
    
    def calculate_comprehensive_scores(self) -> Dict:
        """반감기 사이클을 포함한 종합 점수 계산"""
        
        # 1. 반감기 사이클 신호 (30% 비중)
        halving_signal = self.calculate_halving_signal()
        cycle_info = halving_signal['cycle_info']
        
        # 2. 과열도 지표들 (70% 중 일부)
        heat_indicators = {}
        heat_score = halving_signal['heat_contribution']  # 반감기가 기여하는 과열도
        
        # Pi Cycle Top
        pi_cycle = self.check_pi_cycle_top()
        heat_indicators['pi_cycle_top'] = pi_cycle
        if pi_cycle:
            heat_score += self.heat_indicators_weight['pi_cycle_top'] * 100
        
        # NUPL
        nupl = self.estimate_nupl()
        nupl_triggered = nupl > 0.75
        heat_indicators['nupl'] = {'triggered': nupl_triggered, 'value': nupl}
        if nupl_triggered:
            heat_score += self.heat_indicators_weight['nupl'] * 100
        
        # RSI
        rsi = self.get_weekly_rsi()
        rsi_triggered = rsi > 85
        heat_indicators['rsi_weekly'] = {'triggered': rsi_triggered, 'value': rsi}
        if rsi_triggered:
            heat_score += self.heat_indicators_weight['rsi_weekly'] * 100
        
        # Google Trends
        trends = self.get_google_trends_score()
        trends_triggered = trends > 0.7
        heat_indicators['google_trends'] = {'triggered': trends_triggered, 'value': trends}
        if trends_triggered:
            heat_score += self.heat_indicators_weight['google_trends'] * 100
        
        # 김치 프리미엄
        kimchi = self.calculate_kimchi_premium()
        kimchi_triggered = kimchi > 10
        heat_indicators['kimchi_premium'] = {'triggered': kimchi_triggered, 'value': kimchi}
        if kimchi_triggered:
            heat_score += self.heat_indicators_weight['kimchi_premium'] * 100
        
        # 3. 축적도 지표들 (70% 중 일부)
        acc_indicators = {}
        acc_score = halving_signal['acc_contribution']  # 반감기가 기여하는 축적도
        
        # Fear & Greed
        fear_greed = self.get_fear_greed_index()
        fear_triggered = fear_greed < 30
        acc_indicators['fear_greed'] = {'triggered': fear_triggered, 'value': fear_greed}
        if fear_triggered:
            acc_score += self.accumulation_indicators_weight['fear_greed'] * 100
        
        # 거래소 잔고
        exchange_trend = self.estimate_exchange_balance_trend()
        exchange_triggered = exchange_trend > 0.3
        acc_indicators['exchange_balance'] = {'triggered': exchange_triggered, 'value': exchange_trend}
        if exchange_triggered:
            acc_score += self.accumulation_indicators_weight['exchange_balance'] * 100
        
        # 장기 보유자
        lth = self.estimate_long_term_holder_accumulation()
        lth_triggered = lth > 0.6
        acc_indicators['long_term_holder'] = {'triggered': lth_triggered, 'value': lth}
        if lth_triggered:
            acc_score += self.accumulation_indicators_weight['long_term_holder'] * 100
        
        return {
            'halving_cycle': cycle_info,
            'heat_score': min(heat_score, 100),
            'heat_indicators': heat_indicators,
            'accumulation_score': min(acc_score, 100),
            'accumulation_indicators': acc_indicators
        }
    
    @property
    def halving_dates(self) -> Dict[int, str]:
        """반감기 날짜 딕셔너리 반환 (문자열 형태)"""
        result = {}
        for h in self.halvings:
            date_obj = h['date']
            if isinstance(date_obj, datetime):
                result[h['number']] = date_obj.isoformat()
            else:
                result[h['number']] = str(date_obj)
        return result
    
    def get_action_recommendation(self, scores: Dict) -> Dict:
        """종합 점수 기반 행동 권고"""
        heat_score = scores['heat_score']
        acc_score = scores['accumulation_score']
        cycle_phase = scores['halving_cycle']['phase']
        
        # 과열도 액션
        if heat_score < 30:
            heat_action = "홀드"
        elif heat_score < 50:
            heat_action = "20% 청산 권장"
        elif heat_score < 70:
            heat_action = "누적 50% 청산 권장"
        elif heat_score < 85:
            heat_action = "누적 80% 청산 권장"
        else:
            heat_action = "완전 청산 권장"
        
        # 축적도 액션
        if acc_score < 30:
            acc_action = "대기"
        elif acc_score < 50:
            acc_action = "소량 매수 (DCA $1000/주)"
        elif acc_score < 70:
            acc_action = "적극 매수 (DCA $1500/주)"
        else:
            acc_action = "최대 매수 (DCA $2000/주)"
        
        # 반감기 사이클 기반 종합 권고
        if cycle_phase in ['late-bull', 'distribution']:
            overall_action = "⚠️ 매도 우선 - 반감기 사이클 상 분산 국면"
        elif cycle_phase in ['accumulation', 'late-bear']:
            overall_action = "💎 매수 우선 - 반감기 사이클 상 축적 국면"
        elif cycle_phase in ['early-bull', 'mid-bull']:
            overall_action = "✅ 보유 유지 - 반감기 사이클 상 상승 국면"
        else:
            overall_action = "⏸️ 관망 - 반감기 사이클 상 중립 국면"
        
        return {
            'heat_action': heat_action,
            'accumulation_action': acc_action,
            'overall_action': overall_action,
            'heat_level': int(heat_score / 20),  # 0-5 레벨
            'accumulation_level': int(acc_score / 25)  # 0-4 레벨
        }
    
    def send_notification(self, title: str, message: str):
        """데스크톱 알림 발송"""
        try:
            notification.notify(
                title=title,
                message=message,
                app_icon=None,
                timeout=10
            )
            logger.info(f"📢 알림: {title} - {message}")
        except Exception as e:
            logger.error(f"알림 발송 실패: {e}")
    
    def check_and_alert(self):
        """지표 확인 및 알람 발송"""
        # 가격 정보
        btc_usd = self.get_bitcoin_price_usd()
        btc_krw = self.get_bitcoin_price_krw()
        
        # 종합 점수 계산
        scores = self.calculate_comprehensive_scores()
        actions = self.get_action_recommendation(scores)
        
        # 콘솔 출력
        print("\n" + "="*70)
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"💵 BTC/USD: ${btc_usd:,.0f} | 🇰🇷 BTC/KRW: ₩{btc_krw:,.0f}")
        print("-"*70)
        
        # 반감기 사이클 정보
        cycle = scores['halving_cycle']
        print(f"⏰ 반감기 사이클 (30% 비중)")
        print(f"   현재 국면: {cycle['phase']} (4차 반감기 후 {cycle['months_since_halving']:.1f}개월)")
        print(f"   사이클 위치: {cycle['cycle_position']:.1f}%")
        print(f"   권고사항: {cycle['recommendation']}")
        print(f"   다음 반감기까지: {cycle['months_to_next_halving']:.1f}개월")
        
        print("-"*70)
        print(f"🔥 과열도: {scores['heat_score']:.1f}% → {actions['heat_action']}")
        print(f"💎 축적도: {scores['accumulation_score']:.1f}% → {actions['accumulation_action']}")
        print("-"*70)
        print(f"🎯 종합 권고: {actions['overall_action']}")
        print("="*70)
        
        # 레벨 변경시 알림
        if actions['heat_level'] != self.last_heat_level:
            self.send_notification(
                f"🔥 과열도 레벨 {actions['heat_level']}",
                f"점수: {scores['heat_score']:.0f}%\n{actions['heat_action']}"
            )
            self.last_heat_level = actions['heat_level']
        
        if actions['accumulation_level'] != self.last_accumulation_level:
            self.send_notification(
                f"💎 축적도 레벨 {actions['accumulation_level']}",
                f"점수: {scores['accumulation_score']:.0f}%\n{actions['accumulation_action']}"
            )
            self.last_accumulation_level = actions['accumulation_level']
        
        # 반감기 국면 변경시 알림
        if cycle['phase'] != self.last_halving_phase:
            self.send_notification(
                f"⏰ 반감기 사이클 국면 전환",
                f"새로운 국면: {cycle['phase']}\n{cycle['recommendation']}"
            )
            self.last_halving_phase = cycle['phase']
        
        return scores, actions

def main():
    """메인 실행"""
    print("🚀 비트코인 투자 전략 시스템 (반감기 사이클 포함)")
    print("="*70)
    print("⏰ 반감기 사이클: 30% 비중")
    print("📊 기술적 지표: 70% 비중")
    print("="*70)
    
    system = BitcoinHalvingStrategy()
    
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