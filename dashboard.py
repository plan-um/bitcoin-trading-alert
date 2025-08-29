#!/usr/bin/env python3
"""
비트코인 투자 전략 웹 대시보드
실시간 모니터링 UI
"""

from flask import Flask, render_template, jsonify
from flask_cors import CORS
import threading
import time
from datetime import datetime
import json
import os
from bitcoin_complete_system import BitcoinStrategySystem

app = Flask(__name__)
CORS(app)

# 전역 시스템 인스턴스
system = BitcoinStrategySystem()
latest_data = {}
historical_data = []

def update_data():
    """백그라운드에서 데이터 업데이트"""
    global latest_data, historical_data
    
    while True:
        try:
            # 데이터 수집
            btc_usd = system.get_bitcoin_price_usd()
            btc_krw = system.get_bitcoin_price_krw()
            
            # 과열도 계산
            heat_score, heat_indicators, heat_details = system.calculate_heat_score()
            heat_level, heat_action = system.get_heat_action(heat_score)
            
            # 축적도 계산
            acc_score, acc_indicators, acc_details = system.calculate_accumulation_score()
            fear_greed = acc_details.get('fear_greed_value', 50)
            acc_level, acc_action = system.get_accumulation_action(acc_score, fear_greed)
            
            # 최신 데이터 저장
            latest_data = {
                'timestamp': datetime.now().isoformat(),
                'prices': {
                    'usd': btc_usd,
                    'krw': btc_krw,
                    'kimchi_premium': heat_details.get('kimchi_value', 0)
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
                            'value': fear_greed
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
                }
            }
            
            # 히스토리 추가 (최대 100개 유지)
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
            
        except Exception as e:
            print(f"데이터 업데이트 오류: {e}")
        
        # 5분마다 업데이트
        time.sleep(300)

@app.route('/')
def index():
    """메인 대시보드 페이지"""
    return render_template('dashboard.html')

@app.route('/api/data')
def get_data():
    """현재 데이터 API"""
    return jsonify(latest_data)

@app.route('/api/history')
def get_history():
    """히스토리 데이터 API"""
    return jsonify(historical_data)

@app.route('/api/refresh')
def refresh_data():
    """강제 새로고침"""
    threading.Thread(target=update_single_data).start()
    return jsonify({'status': 'refreshing'})

def update_single_data():
    """단일 데이터 업데이트 (강제 새로고침용)"""
    global latest_data
    
    try:
        btc_usd = system.get_bitcoin_price_usd()
        btc_krw = system.get_bitcoin_price_krw()
        
        heat_score, heat_indicators, heat_details = system.calculate_heat_score()
        heat_level, heat_action = system.get_heat_action(heat_score)
        
        acc_score, acc_indicators, acc_details = system.calculate_accumulation_score()
        fear_greed = acc_details.get('fear_greed_value', 50)
        acc_level, acc_action = system.get_accumulation_action(acc_score, fear_greed)
        
        latest_data = {
            'timestamp': datetime.now().isoformat(),
            'prices': {
                'usd': btc_usd,
                'krw': btc_krw,
                'kimchi_premium': heat_details.get('kimchi_value', 0)
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
                        'value': fear_greed
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
            }
        }
    except Exception as e:
        print(f"데이터 업데이트 오류: {e}")

if __name__ == '__main__':
    # 초기 데이터 로드
    if os.path.exists('dashboard_data.json'):
        try:
            with open('dashboard_data.json', 'r') as f:
                latest_data = json.load(f)
        except:
            print("기존 데이터 파일 로드 실패, 새로 시작합니다.")
            latest_data = {}
    
    # 초기 데이터 업데이트
    print("초기 데이터 수집 중...")
    update_single_data()
    
    # 백그라운드 업데이트 시작
    update_thread = threading.Thread(target=update_data, daemon=True)
    update_thread.start()
    
    print("🚀 대시보드 서버 시작: http://localhost:5000")
    print("✅ 브라우저에서 접속하세요!")
    print("종료: Ctrl+C")
    app.run(debug=False, port=5000, host='0.0.0.0')