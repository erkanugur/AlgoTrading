import time
import urllib.parse
from typing import Optional, Dict, Any, List
from requests import Request, Session, Response
import hmac
import pandas as pd 
import numpy as np
class AlgoTrading:
    
    """
   Trading on FTX

   Examples
   --------
   algotrading = AlgoTrading(api_key,api_secret)
   
   """
    
    _endpoint = 'https://ftx.com/api/' 
    
    def __init__(self, api_key=None, api_secret=None) :
        
        self._session = Session()
        self._api_key = api_key
        self._api_secret = api_secret
        
    def _get(self, path, params = None):
        """helps to create get request"""
        
        return self._request('GET', path, params=params)
    
    def _post(self, path, params = None):
        """helps to create post request"""
        return self._request('POST', path, json=params)
    
    def _request(self, method, path, **kwargs):
        """sign to account for every request and return response"""
        request = Request(method, self._endpoint + path, **kwargs)
        self._sign_request(request)
        response = self._session.send(request.prepare())
        
        return self._process_response(response)
    
    
    def _sign_request(self, request: Request):
        """helps to sign in account"""
        ts = int(time.time() * 1000)
        prepared = request.prepare()
        signature_payload = f'{ts}{prepared.method}{prepared.path_url}'.encode()
        if prepared.body:
            signature_payload += prepared.body
        signature = hmac.new(self._api_secret.encode(), signature_payload, 'sha256').hexdigest()
        request.headers['FTX-KEY'] = self._api_key
        request.headers['FTX-SIGN'] = signature
        request.headers['FTX-TS'] = str(ts)



    def _process_response(self, response: Response):
        """helps to check response, if there is any error throw an exception otherwise return output as json format"""
        try:
            data = response.json()
        except ValueError:
            response.raise_for_status()
            raise
        else:
            if not data['success']:
                raise Exception(data['error'])
            return data['result']
    
    
    def get_account_info(self):
        """gets account info"""
        return self._get(f'account')
        
    
    
    def get_available_currencies(self,market_type:str = 'spot'):
        
        """gets available currency pairs on FTX
        
        
           Examples
           --------
           available_currency_list = self.get_available_currencies(market_type = 'spot')
           
           
        
        """
        
        path = 'markets'
        
        markets = pd.DataFrame(self._get(path))
        
        if market_type =='spot':
            
            available_currency_list = markets.loc[markets['type']==market_type,'name'].apply(lambda x : ''.join(x.split('-')) if '-' in x else ''.join(x.split('/'))).tolist()
           
        elif market_type =='future':
            
            available_currency_list = markets.loc[markets['type']==market_type,'name'].apply(lambda x : ''.join(x.split('-')) if '-' in x else ''.join(x.split('/'))).tolist()
        
        
        elif market_type =='all':
            
            available_currency_list = markets['name'].apply(lambda x : ''.join(x.split('-')) if '-' in x else ''.join(x.split('/'))).tolist()
            
            
        else:
            raise Exception('Please enter valid market type (spot,future,all)...')
            
        
        
        return available_currency_list
    
    
    
    def check_market_type(self,base_currency:str,quote_currency:str):
        
        """checks market type with respect to currency pair
        
        
           Examples
           --------
           self.get_available_currencies(base_currency = 'BTC',quote_currency = 'USDT')
        """
        
        pair,reverse_pair = base_currency+quote_currency,quote_currency+base_currency
        
        future_currency_list = self.get_available_currencies(market_type = 'future')
        
        if pair in future_currency_list or reverse_pair in future_currency_list:
            raise Exception('Currency pair belongs to future market, service is only available for spot markets')
            
        
        
    
    def get_symbol_and_reverse(self,base_currency:str,quote_currency:str,market_type:str ='spot'):
        """transforms base and quote currencies to pair with respect to market_type
           
           Examples
           --------
           self.get_symbol_and_reverse(base_currency = 'BTC',quote_currency = 'USDT',market_type ='spot')
           
           Returns
           -------
           
           'BTC/USDT'
        
        """
        
        if market_type =='spot':
            return base_currency + "/" + quote_currency,quote_currency + "/" + base_currency
        elif market_type =='future':
            return base_currency + "-" + quote_currency,quote_currency + "-"  + base_currency
        else:
             raise Exception('Please enter valid market type (future,spot)...')
            
    
    
    

    def create_market_order(self, action: str, base_currency: str, quote_currency: str, amount: float):
        
        """creates market order
           
           
           Examples
           --------
           self.create_market_order('sell', 'AVAX', 'USDT', 1000)
           
           Returns
           -------
           
           {'total': 88649.99035000002, 'price': 88.64999035000002, 'currency': 'USDT'}
        
        """
        
        symbol,reverse_symbol = self.get_symbol_and_reverse(base_currency,quote_currency,market_type = 'spot')
        
        pair,reverse_pair = base_currency+quote_currency,quote_currency+base_currency
    
        spot_currency_list = self.get_available_currencies(market_type = 'spot')
        
        response = self.simulate_market_price(action,base_currency,quote_currency,amount)
        
        market = symbol if pair in spot_currency_list else reverse_symbol
        
        amount = amount if pair in spot_currency_list else response['total']
        
        
        
        self._post('orders', {'market': market,
                                     'side': action,
                                     'price':None,
                                     'size': amount,
                                     'type': 'market'
                                     })
        
        return response
       
      
    def create_limit_order(self, action: str, base_currency: str, quote_currency: str, amount: float,price:float,number_of_iceberg_order:int):
        
         
        """creates limit order
           
           
           Examples
           --------
           self.create_limit_order('sell', 'AVAX', 'USDT', 100, 0.2, 5)
           
           Returns
           -------
           
           [ {'Order_size': 4.0, 'Price': 0.2, 'Currency': 'USDT'},
             {'Order_size': 4.0, 'Price': 0.2, 'Currency': 'USDT'},
             {'Order_size': 4.0, 'Price': 0.2, 'Currency': 'USDT'},
             {'Order_size': 4.0, 'Price': 0.2, 'Currency': 'USDT'},
             {'Order_size': 4.0, 'Price': 0.2, 'Currency': 'USDT'}]
        
        """
        
        response_list = []
        
        symbol,reverse_symbol = self.get_symbol_and_reverse(base_currency,quote_currency,market_type = 'spot')
        
        pair,reverse_pair = base_currency+quote_currency,quote_currency+base_currency
      
        spot_currency_list = self.get_available_currencies(market_type = 'spot')
        
        market = symbol if pair in spot_currency_list else reverse_symbol
        
        amount = amount if pair in spot_currency_list else amount*price
        
        price = price if pair in spot_currency_list else 1/price
        
        
        for order in range(number_of_iceberg_order):
            
            response = {}
            order_size = amount/number_of_iceberg_order
            
            response['Order_size'] = order_size*price
            response['Price'] = price
            response['Currency'] = quote_currency
            
            response_list.append(response)
        
            self._post('orders', {'market': market,
                                         'side': action,
                                         'price':price,
                                         'size': order_size,
                                         'type': 'limit'
                                         })
    
    
        return response_list
    
    
    def simulate_market_price(self,action:str,base_currency:str,quote_currency:str,amount:float,return_limit_order_info:bool = False,iceberg_order:int = None):
        
        """simulates market orders
           
           
           Examples
           --------
           self.simulate_market_price('buy', 'BTC', 'USDT', 10)
           
           Returns
           -------
           {'total': 425157.00210000004, 'price': 42515.70021, 'currency': 'USDT'}
           
           Reverse currency pair can also be used:
           
           Examples
           --------
           self.simulate_market_price('buy', 'USDT', 'BTC', 10)
           
           Returns
           -------
           {'total': 7.061732161691308, 'price': 2.353910720563769e-05, 'currency': 'BTC'}
          
        
        """
        
        symbol,reverse_symbol = self.get_symbol_and_reverse(base_currency,quote_currency,market_type = 'spot')
        
        pair,reverse_pair = base_currency+quote_currency,quote_currency+base_currency
        
        self.check_market_type(base_currency,quote_currency)
        
        spot_currency_list = self.get_available_currencies(market_type = 'spot')
        
        depth = 100
        path = 'markets/'+symbol+f'/orderbook?depth={depth}' if pair in spot_currency_list else 'markets/'+reverse_symbol+f'/orderbook?depth={depth}'
        
        response = {}
        
        limit_order_info = {}
        
        if pair in spot_currency_list: # not reverse symbol case
            
            df_orderbook = pd.DataFrame(self._get(path))
            df_orderbook[['Bid_Price','Bid_Quant']] = pd.DataFrame(df_orderbook.bids.tolist(), index= df_orderbook.index)
            df_orderbook[['Ask_Price','Ask_Quant']] = pd.DataFrame(df_orderbook.asks.tolist(), index= df_orderbook.index)
            df_orderbook.drop(['bids','asks'],inplace=True,axis=1)
            
        else: # reverse symbol case
            df_orderbook = pd.DataFrame(self._get(path))
            df_orderbook[['Ask_Price','Ask_Quant']] = pd.DataFrame(df_orderbook.bids.tolist(), index= df_orderbook.index)
            df_orderbook[['Bid_Price','Bid_Quant']] = pd.DataFrame(df_orderbook.asks.tolist(), index= df_orderbook.index)
            df_orderbook.drop(['bids','asks'],inplace=True,axis=1)
            
            df_orderbook['Ask_Quant']  =  df_orderbook['Ask_Quant'] * df_orderbook['Ask_Price']
            df_orderbook['Bid_Quant']  =  df_orderbook['Bid_Quant'] * df_orderbook['Bid_Price']
            df_orderbook[['Ask_Price','Bid_Price']]  =  1 / df_orderbook[['Ask_Price','Bid_Price']] 
            
            
        if action == 'buy':
    
            df_orderbook['Ask_Quant_Cumsum'] = df_orderbook['Ask_Quant'].cumsum()
           
            try:
                index_buy = df_orderbook.loc[df_orderbook['Ask_Quant_Cumsum']>=amount,'Ask_Quant_Cumsum'].index.tolist()[0]
            except:
                raise Exception(f'Your buy amount is not offset by order book in {depth} depths')
            
            df_orderbook.loc[index_buy,'Ask_Quant'] = df_orderbook.loc[index_buy,'Ask_Quant']-(df_orderbook.loc[index_buy,'Ask_Quant_Cumsum']-amount)
            
            df_orderbook['Ask_Quant_Cumsum'] = df_orderbook['Ask_Quant'].cumsum()
            
            df_orderbook['Weighted_Ask_Price'] = (df_orderbook['Ask_Price']*df_orderbook['Ask_Quant']).cumsum() / df_orderbook['Ask_Quant_Cumsum']
            
           
            
            if return_limit_order_info:
                
                response['Order_size'] = df_orderbook.loc[index_buy,'Weighted_Ask_Price'] * amount
                response['Price'] = df_orderbook.loc[index_buy,'Weighted_Ask_Price']
                response['Currency'] = quote_currency
                
                limit_order_info['Action']  = action
                limit_order_info['Base_currency'] = base_currency
                limit_order_info['Quote_currency'] = quote_currency
                limit_order_info['Amount'] = amount
                limit_order_info['Price'] = df_orderbook.loc[index_buy,'Ask_Price']
                limit_order_info['Number_of_iceberg_order'] = iceberg_order
                
            else:
                response['total'] = df_orderbook.loc[index_buy,'Weighted_Ask_Price'] * amount
                response['price'] = df_orderbook.loc[index_buy,'Weighted_Ask_Price']
                response['currency'] = quote_currency
                
           
              
              
            
            if not return_limit_order_info:
                
                return response
            
            else: 
                return response,limit_order_info 
            
        elif action == 'sell':
            
            df_orderbook['Bid_Quant_Cumsum'] = df_orderbook['Bid_Quant'].cumsum()
            
            try:
                index_sell = df_orderbook.loc[df_orderbook['Bid_Quant_Cumsum']>=amount,'Bid_Quant_Cumsum'].index.tolist()[0]   
            except:
                raise Exception(f'Your sell amount is not offset by order book in {depth} depths')
             
            df_orderbook.loc[index_sell,'Bid_Quant'] = df_orderbook.loc[index_sell,'Bid_Quant']-(df_orderbook.loc[index_sell,'Bid_Quant_Cumsum']-amount)
            
            df_orderbook['Bid_Quant_Cumsum'] = df_orderbook['Bid_Quant'].cumsum()
            
            df_orderbook['Weighted_Bid_Price'] = (df_orderbook['Bid_Price']*df_orderbook['Bid_Quant']).cumsum() / df_orderbook['Bid_Quant_Cumsum']
            
            
            
            if return_limit_order_info:
                
                response['Order_size'] = df_orderbook.loc[index_sell,'Weighted_Bid_Price'] * amount
                response['Price'] = df_orderbook.loc[index_sell,'Weighted_Bid_Price']
                response['Currency'] = quote_currency
                
                limit_order_info['Action']  = action
                limit_order_info['Base_currency'] = base_currency
                limit_order_info['Quote_currency'] = quote_currency
                limit_order_info['Amount'] = amount
                limit_order_info['Price'] = df_orderbook.loc[index_sell,'Bid_Price']
                limit_order_info['Number_of_iceberg_order'] = iceberg_order
                
                
            else:
                response['total'] = df_orderbook.loc[index_sell,'Weighted_Bid_Price'] * amount
                response['price'] = df_orderbook.loc[index_sell,'Weighted_Bid_Price']
                response['currency'] = quote_currency
              
            
            if not return_limit_order_info:
                
                return response
            
            else: 
                return response,limit_order_info 
        
    
    