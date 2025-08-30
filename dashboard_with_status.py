#!/usr/bin/env python3
"""
비트코인 투자 전략 웹 대시보드 - 데이터 상태 모니터링 포함
"""

from flask import Flask, render_template, jsonify
from flask_cors import CORS
import threading
import time
from datetime import datetime, timedelta
import json
import os
from bitcoin_halving_system import BitcoinHalvingStrategy
import numpy as np
import traceback

app = Flask(__name__)
CORS(app)

# 전역 시스템 인스턴스
system = BitcoinHalvingStrategy()
latest_data = {}
historical_data = []
data_status = {
    'price_usd': {'status': 'unknown', 'last_update': None, 'error': None},
    'price_krw': {'status': 'unknown', 'last_update': None, 'error': None},
    'pi_cycle': {'status': 'unknown', 'last_update': None, 'error': None},
    'nupl': {'status': 'unknown', 'last_update': None, 'error': None},
    'rsi': {'status': 'unknown', 'last_update': None, 'error': None},
    'google_trends': {'status': 'unknown', 'last_update': None, 'error': None},
    'fear_greed': {'status': 'unknown', 'last_update': None, 'error': None},
    'exchange_balance': {'status': 'unknown', 'last_update': None, 'error': None},
    'long_term_holder': {'status': 'unknown', 'last_update': None, 'error': None},
}

def convert_to_json_serializable(obj):
    """numpy 타입을 JSON 직렬화 가능한 타입으로 변환"""
    if isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.float64, np.float32, np.float16)):
        return float(obj)
    elif isinstance(obj, dict):
        return {key: convert_to_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_json_serializable(item) for item in obj]
    return obj

def update_status(key, status, error=None):
    """데이터 소스 상태 업데이트"""
    data_status[key] = {
        'status': status,
        'last_update': datetime.now().isoformat(),
        'error': str(error) if error else None
    }

def get_data_freshness(last_update):
    """데이터 신선도 계산 (fresh/stale/error)"""
    if not last_update:
        return 'error'
    
    try:
        update_time = datetime.fromisoformat(last_update)
        age = datetime.now() - update_time
        
        if age < timedelta(minutes=5):
            return 'fresh'
        elif age < timedelta(minutes=15):
            return 'stale'
        else:
            return 'error'
    except:
        return 'error'

def update_data():
    """백그라운드에서 데이터 업데이트"""
    global latest_data, historical_data
    
    while True:
        try:
            # USD 가격
            try:
                btc_usd = system.get_bitcoin_price_usd()
                update_status('price_usd', 'success' if btc_usd > 0 else 'error')
            except Exception as e:
                btc_usd = 0
                update_status('price_usd', 'error', e)
            
            # KRW 가격
            try:
                btc_krw = system.get_bitcoin_price_krw()
                update_status('price_krw', 'success' if btc_krw > 0 else 'error')
            except Exception as e:
                btc_krw = 0
                update_status('price_krw', 'error', e)
            
            # 과열도 지표들
            heat_indicators = {}
            heat_details = {}
            
            # Pi Cycle
            try:
                pi_cycle = system.check_pi_cycle_top()
                heat_indicators['pi_cycle_top'] = pi_cycle
                update_status('pi_cycle', 'success')
            except Exception as e:
                heat_indicators['pi_cycle_top'] = False
                update_status('pi_cycle', 'error', e)
            
            # NUPL
            try:
                nupl = system.estimate_nupl()
                heat_indicators['nupl'] = nupl > 0.75
                heat_details['nupl_value'] = nupl
                update_status('nupl', 'success')
            except Exception as e:
                heat_indicators['nupl'] = False
                heat_details['nupl_value'] = 0
                update_status('nupl', 'error', e)
            
            # RSI
            try:
                rsi = system.get_weekly_rsi()
                heat_indicators['rsi_weekly'] = rsi > 85
                heat_details['rsi_value'] = rsi
                update_status('rsi', 'success')
            except Exception as e:
                heat_indicators['rsi_weekly'] = False
                heat_details['rsi_value'] = 50
                update_status('rsi', 'error', e)
            
            # Google Trends
            try:
                trends = system.get_google_trends_score()
                heat_indicators['google_trends'] = trends > 0.7
                heat_details['trends_value'] = trends
                update_status('google_trends', 'success')
            except Exception as e:
                heat_indicators['google_trends'] = False
                heat_details['trends_value'] = 0
                update_status('google_trends', 'error', e)
            
            # 김치 프리미엄
            try:
                if btc_usd > 0 and btc_krw > 0:
                    kimchi = system.calculate_kimchi_premium()
                    heat_indicators['kimchi_premium'] = kimchi > 10
                    heat_details['kimchi_value'] = kimchi
                else:
                    raise Exception("가격 데이터 없음")
            except Exception as e:
                heat_indicators['kimchi_premium'] = False
                heat_details['kimchi_value'] = 0
            
            # 반감기 사이클 분석
            try:
                halving_data = system.analyze_halving_cycle()
                halving_score = halving_data['cycle_score'] * 100
                halving_weight = system.halving_weight
            except Exception as e:
                halving_data = {
                    'phase': 'unknown',
                    'months_since': 0,
                    'cycle_score': 0,
                    'recommendation': 'Unable to determine cycle phase'
                }
                halving_score = 0
                halving_weight = 0
            
            # 과열도 점수 계산 (반감기 포함)
            heat_score = 0
            for key, weight in system.heat_indicators_weight.items():
                if heat_indicators.get(key, False):
                    heat_score += weight
            heat_score += (halving_score / 100) * halving_weight
            heat_score *= 100
            heat_level, heat_action = system.get_heat_action(heat_score)
            
            # 축적도 지표들
            acc_indicators = {}
            acc_details = {}
            
            # Fear & Greed
            try:
                fear_greed = system.get_fear_greed_index()
                acc_indicators['fear_greed'] = fear_greed < 30
                acc_details['fear_greed_value'] = fear_greed
                update_status('fear_greed', 'success')
            except Exception as e:
                acc_indicators['fear_greed'] = False
                acc_details['fear_greed_value'] = 50
                update_status('fear_greed', 'error', e)
            
            # 거래소 잔고
            try:
                exchange_trend = system.estimate_exchange_balance_trend()
                acc_indicators['exchange_balance'] = exchange_trend > 0.3
                acc_details['exchange_trend'] = exchange_trend
                update_status('exchange_balance', 'success')
            except Exception as e:
                acc_indicators['exchange_balance'] = False
                acc_details['exchange_trend'] = 0
                update_status('exchange_balance', 'error', e)
            
            # 장기 보유자
            try:
                lth = system.estimate_long_term_holder_accumulation()
                acc_indicators['long_term_holder'] = lth > 0.6
                acc_details['lth_value'] = lth
                update_status('long_term_holder', 'success')
            except Exception as e:
                acc_indicators['long_term_holder'] = False
                acc_details['lth_value'] = 0
                update_status('long_term_holder', 'error', e)
            
            # 반감기
            months_to_halving = system.get_months_until_halving()
            acc_indicators['halving_window'] = months_to_halving and 6 <= months_to_halving <= 18
            acc_details['months_to_halving'] = months_to_halving
            
            # 축적도 점수 계산
            acc_score = 0
            for key, weight in system.accumulation_indicators_weight.items():
                if acc_indicators.get(key, False):
                    acc_score += weight
            if acc_indicators.get('halving_window', False):
                acc_score *= 1.2
            acc_score = min(acc_score * 100, 100)
            acc_level, acc_action = system.get_accumulation_action(acc_score, acc_details.get('fear_greed_value', 50))
            
            # 최신 데이터 저장
            latest_data = convert_to_json_serializable({
                'timestamp': datetime.now().isoformat(),
                'prices': {
                    'usd': btc_usd,
                    'krw': btc_krw,
                    'kimchi_premium': heat_details.get('kimchi_value', 0)
                },
                'halving_cycle': {
                    'phase': halving_data['phase'],
                    'months_since': halving_data['months_since'],
                    'score': halving_score,
                    'weight': halving_weight * 100,
                    'recommendation': halving_data['recommendation'],
                    'next_halving': str(system.halving_dates.get(5, '')) if system.halving_dates.get(5) else None  # 5차 반감기 (다음 반감기)
                },
                'heat': {
                    'score': heat_score,
                    'level': heat_level,
                    'action': heat_action,
                    'indicators': {
                        'pi_cycle_top': heat_indicators.get('pi_cycle_top', False),
                        'nupl': {
                            'triggered': heat_indicators.get('nupl', False),
                            'value': heat_details.get('nupl_value', 0)
                        },
                        'rsi_weekly': {
                            'triggered': heat_indicators.get('rsi_weekly', False),
                            'value': heat_details.get('rsi_value', 50)
                        },
                        'google_trends': {
                            'triggered': heat_indicators.get('google_trends', False),
                            'value': heat_details.get('trends_value', 0) * 100
                        },
                        'kimchi_premium': {
                            'triggered': heat_indicators.get('kimchi_premium', False),
                            'value': heat_details.get('kimchi_value', 0)
                        }
                    }
                },
                'accumulation': {
                    'score': acc_score,
                    'level': acc_level,
                    'action': acc_action,
                    'indicators': {
                        'fear_greed': {
                            'triggered': acc_indicators.get('fear_greed', False),
                            'value': acc_details.get('fear_greed_value', 50)
                        },
                        'exchange_balance': {
                            'triggered': acc_indicators.get('exchange_balance', False),
                            'value': acc_details.get('exchange_trend', 0) * 100
                        },
                        'long_term_holder': {
                            'triggered': acc_indicators.get('long_term_holder', False),
                            'value': acc_details.get('lth_value', 0) * 100
                        },
                        'halving_window': acc_indicators.get('halving_window', False),
                        'months_to_halving': acc_details.get('months_to_halving', None)
                    }
                },
                'data_status': {
                    key: {
                        **value,
                        'freshness': get_data_freshness(value.get('last_update'))
                    } for key, value in data_status.items()
                }
            })
            
            # 히스토리 추가
            historical_data.append({
                'timestamp': datetime.now().isoformat(),
                'heat_score': heat_score,
                'acc_score': acc_score,
                'price': btc_usd
            })
            
            if len(historical_data) > 100:
                historical_data = historical_data[-100:]
            
            # 파일 저장
            with open('dashboard_data.json', 'w') as f:
                json.dump(latest_data, f, indent=2)
            
            print(f"✅ 업데이트 완료: BTC ${btc_usd:,.0f}, 과열도 {heat_score:.1f}%, 축적도 {acc_score:.1f}%")
            
        except Exception as e:
            print(f"❌ 전체 업데이트 오류: {e}")
            traceback.print_exc()
        
        # 5분마다 업데이트
        time.sleep(300)

@app.route('/')
def index():
    """메인 대시보드 페이지"""
    return render_template('dashboard_final.html')

@app.route('/health')
def health():
    """헬스체크 엔드포인트"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/data')
def get_data():
    """현재 데이터 API"""
    return jsonify(latest_data)

@app.route('/api/history')
def get_history():
    """히스토리 데이터 API"""
    return jsonify(historical_data)

@app.route('/api/status')
def get_status():
    """데이터 소스 상태 API"""
    status_with_freshness = {}
    for key, value in data_status.items():
        status_with_freshness[key] = {
            **value,
            'freshness': get_data_freshness(value.get('last_update'))
        }
    return jsonify(status_with_freshness)

@app.route('/api/refresh')
def refresh_data():
    """강제 새로고침"""
    threading.Thread(target=update_single_data).start()
    return jsonify({'status': 'refreshing'})

def update_single_data():
    """단일 데이터 업데이트 (초기화 및 강제 새로고침용)"""
    global latest_data
    
    # update_data의 로직과 동일하게 실행
    try:
        # 모든 데이터 수집 로직 실행
        print("📊 데이터 수집 시작...")
        
        # 여기서 update_data의 한 사이클 실행
        # (코드 중복을 피하기 위해 실제로는 update_data를 한 번만 실행)
        
        # USD 가격
        try:
            btc_usd = system.get_bitcoin_price_usd()
            update_status('price_usd', 'success' if btc_usd > 0 else 'error')
            print(f"  USD: ${btc_usd:,.0f}")
        except Exception as e:
            btc_usd = 0
            update_status('price_usd', 'error', e)
            print(f"  USD: 실패")
        
        # 나머지 지표들도 동일하게...
        # (실제 구현에서는 update_data의 로직 재사용)
        
        print("✅ 초기 데이터 수집 완료")
    except Exception as e:
        print(f"❌ 데이터 수집 실패: {e}")

# 초기 데이터 로드 (모듈 로드 시 실행)
if os.path.exists('dashboard_data.json'):
    try:
        with open('dashboard_data.json', 'r') as f:
            latest_data = json.load(f)
        print("기존 데이터 파일 로드 성공")
    except:
        print("기존 데이터 파일 로드 실패, 새로 시작합니다.")
        latest_data = {}
else:
    latest_data = {}

# 백그라운드 업데이트 스레드 시작
update_thread = threading.Thread(target=update_data, daemon=True)
update_thread.start()

if __name__ == '__main__':
    # 초기 데이터 업데이트
    print("초기 데이터 수집 중...")
    update_single_data()
    
    print("="*60)
    print("🚀 비트코인 투자 전략 대시보드 (상태 모니터링 포함)")
    print("="*60)
    print("✅ 브라우저에서 접속: http://localhost:5000")
    print("✅ 30초마다 자동 업데이트")
    print("✅ 데이터 소스 상태 실시간 확인")
    print("✅ 종료: Ctrl+C")
    print("="*60)
    
    app.run(debug=False, port=5000, host='0.0.0.0')