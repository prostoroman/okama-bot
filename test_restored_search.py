#!/usr/bin/env python3
"""
Test script for restored search dictionary
"""

import sys
import os
import time

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_restored_search():
    """Test the restored search dictionary"""
    
    try:
        from moex_search_embedded import try_fuzzy_search, get_direct_ticker
        print("✅ Module imported successfully")
        
        # Test cases for restored mappings
        test_cases = {
            "Restored MOEX Assets": [
                ("полюс", "PLZL.MOEX"),
                ("полюс золото", "PLZL.MOEX"),
                ("polyus", "PLZL.MOEX"),
                ("сургутнефтегаз преф", "SNGSP.MOEX"),
                ("сургут преф", "SNGSP.MOEX"),
                ("татнефть преф", "TATNP.MOEX"),
                ("tatneft pref", "TATNP.MOEX"),
                ("x5", "FIVE.MOEX"),
                ("х5", "FIVE.MOEX"),
                ("x5 ритейл", "FIVE.MOEX"),
                ("русал", "RUAL.MOEX"),
                ("rusal", "RUAL.MOEX"),
                ("аэрофлот", "AFLT.MOEX"),
                ("aeroflot", "AFLT.MOEX"),
                ("озон", "OZON.MOEX"),
                ("ozon", "OZON.MOEX"),
                ("сегежа", "SELG.MOEX"),
                ("пик", "PIKK.MOEX"),
                ("транснефть", "TRNFP.MOEX"),
                ("втб", "VTBR.MOEX"),
                ("русснефть", "RNFT.MOEX"),
                ("полиметалл", "POLY.MOEX"),
            ],
            
            "Restored US Stocks": [
                ("netflix", "NFLX.US"),
                ("disney", "DIS.US"),
                ("coca-cola", "KO.US"),
            ],
            
            "Restored European": [
                ("volkswagen", "VOW.XETR"),
            ],
            
            "Restored Commodities": [
                ("gold", "XAU.COMM"),
                ("silver", "XAG.COMM"),
                ("oil", "BRENT.COMM"),
                ("copper", "HG.COMM"),
            ],
            
            "Restored Forex": [
                ("eurusd", "EURUSD.FX"),
                ("gbpusd", "GBPUSD.FX"),
                ("usdjpy", "USDJPY.FX"),
                ("usdchf", "USDCHF.FX"),
            ],
            
            "Restored Indices": [
                ("sp500", "SPX.INDX"),
                ("nasdaq", "NDX.INDX"),
                ("dow", "DJI.INDX"),
                ("rts", "RTSI.INDX"),
            ],
            
            "New Additions (kept)": [
                ("система", "AFKS.MOEX"),
                ("vim lqdt", "LQDT.MOEX"),
                ("т-технологии", "T.MOEX"),
                ("allianz", "ALV.XETR"),
                ("deutsche telekom", "DTE.XETR"),
                ("basf", "BAS.XETR"),
                ("rwe", "RWE.XETR"),
                ("munich re", "MUV2.XETR"),
                ("adidas", "ADS.XETR"),
                ("henkel", "HEN3.XETR"),
                ("volkswagen", "VOW3.XETR"),
                ("infineon", "IFX.XETR"),
                ("linde", "LIN.XETR"),
                ("siemens healthineers", "SHL.XETR"),
                ("continental", "CON.XETR"),
                ("hella", "HEI.XETR"),
                ("fresenius medical care", "FME.XETR"),
                ("fresenius", "FRE.XETR"),
                ("binance coin", "BNB-USD.CC"),
                ("solana", "SOL-USD.CC"),
                ("tether", "USDT-USD.CC"),
                ("usd coin", "USDC-USD.CC"),
                ("dogecoin", "DOGE-USD.CC"),
                ("cardano", "ADA-USD.CC"),
                ("tron", "TRX-USD.CC"),
                ("toncoin", "TON-USD.CC"),
            ],
        }
        
        print("\nTesting restored search dictionary...")
        print("=" * 80)
        
        total_tests = 0
        passed_tests = 0
        failed_tests = []
        
        for category, queries in test_cases.items():
            print(f"\n📊 {category}")
            print("-" * 60)
            
            for query, expected_ticker in queries:
                total_tests += 1
                print(f"\nTesting: '{query}'")
                print(f"Expected: {expected_ticker}")
                
                # Test direct ticker lookup
                direct_ticker = get_direct_ticker(query)
                if direct_ticker == expected_ticker:
                    print(f"✅ Direct ticker: {direct_ticker}")
                else:
                    print(f"❌ Direct ticker mismatch: {direct_ticker} != {expected_ticker}")
                
                # Test unified search
                results = try_fuzzy_search(query)
                
                if results:
                    top_result = results[0]
                    symbol = top_result['symbol']
                    source = top_result['source']
                    score = top_result['score']
                    
                    print(f"Search result: {symbol} (source: {source}, score: {score:.3f})")
                    
                    if symbol == expected_ticker and source == 'direct_mapping':
                        print("🎯 Perfect! Direct mapping working correctly")
                        passed_tests += 1
                    elif symbol == expected_ticker:
                        print("✅ Good! Correct ticker found")
                        passed_tests += 1
                    else:
                        print(f"❌ Unexpected result: {symbol}")
                        failed_tests.append((query, expected_ticker, symbol))
                else:
                    print("❌ No results found")
                    failed_tests.append((query, expected_ticker, "No results"))
        
        # Performance test
        print(f"\n{'='*80}")
        print("⚡ PERFORMANCE TEST")
        print(f"{'='*80}")
        
        performance_queries = ["полюс", "x5", "русал", "аэрофлот", "gold", "eurusd", "sp500", "система"]
        
        for query in performance_queries:
            start_time = time.time()
            results = try_fuzzy_search(query)
            end_time = time.time()
            
            duration = (end_time - start_time) * 1000  # Convert to milliseconds
            result_count = len(results)
            source = results[0]['source'] if results else 'none'
            
            print(f"'{query}': {duration:.1f}ms, {result_count} results, source: {source}")
        
        # Summary
        print(f"\n{'='*80}")
        print("📈 RESTORED DICTIONARY TEST SUMMARY")
        print(f"{'='*80}")
        print(f"Total tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {len(failed_tests)}")
        print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for query, expected, actual in failed_tests[:10]:  # Show first 10 failures
                print(f"  '{query}' -> Expected: {expected}, Got: {actual}")
        
        if passed_tests >= total_tests * 0.95:  # 95% success rate
            print(f"\n🎉 EXCELLENT: Restored search dictionary is working perfectly!")
        elif passed_tests >= total_tests * 0.90:  # 90% success rate
            print(f"\n✅ SUCCESS: Restored search dictionary is working well!")
        else:
            print(f"\n❌ FAILURE: Search dictionary still needs work")
        
    except ImportError as e:
        print(f"❌ Failed to import module: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_restored_search()
