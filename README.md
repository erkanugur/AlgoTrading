ALGOTRADING
AlgoTrading class was written to meet some trading needs(get account info, create market and limit order..vs) over the FTX.

Main methods are described in the following flow.
get_available_currencies:
inputs : market_type(String) =[‘spot’,’future’,’all’ ]
outputs: available_currency_list (List)
description : gets all available currency pairs for specific market type 

check_market_type:
inputs : 
•	base_currency (String) = any base currency that listed in FTX
•	quote_currency(String) = any base currency that listed in FTX

outputs: 
description : checks currency pair whether belongs to future market or not. If future markets  raise Exception

create_market_order:
inputs: 
•	 action(String) = Market side of order -> [‘buy’,sell’]
•	 base_currency(String) = any base currency that listed in FTX
•	 quote_currency(String) = any quote currency that listed in FTX
•	 amount(Float) =  Order amount

outputs: 
•	total (Float): Total quantity of quote currency 
•	price (Float): The per-unit cost of the base currency 
•	currency (String): The quote currency

description: creates market order with respect to inputs

create_limit_order:
inputs: 
•	 action(String) = Market side of order -> [‘buy’,sell’]
•	 base_currency(String) = any base currency that listed in FTX
•	 quote_currency(String) = any quote currency that listed in FTX
•	 amount(Float) =  Order amount
•	 Price(Float) = The price of limit order
•	 Number_of_Iceberg_Order(Integer) = The number of iceberg orders between 1 to 5

outputs: 
•	order_size (Float): Total quantity of quote currency 
•	price (Float): The order price  
•	currency (String): The quote currency
description: creates limit order with respect to inputs, if the number of iceberg order is greater than 1, splits the quantity into equal parts and send them separately.

simulate_market_price:
	inputs:
•	action(String) = Market side of order -> [‘buy’,sell’]
•	base_currency(String) = any base currency that listed in FTX
•	quote_currency(String) = any quote currency that listed in FTX
•	amount(Float) =  Order amount
•	return_limit_order_info(Boolean) = If True returns limit order input with respect to calculation about market orders
•	iceberg_order(Integer) = If return_limit_order_info is True, refers to number of iceberg orders between 1 to 5

outputs: 
•	response:
o	order_size (Float): Total quantity of quote currency 
o	price (Float): The order price  
o	currency (String): The quote currency

•	limit_order_info:
o	action(String) = Market side of order -> [‘buy’,sell’]
o	base_currency(String) = any base currency that listed in FTX
o	quote_currency(String) = any quote currency that listed in FTX
o	amount(Float) =  Order amount
o	Price(Float) = The price of limit order
o	Number_of_Iceberg_Order(Integer) = The number of iceberg orders between 1 to 5
description: 
This method is related with simulation and does not send any order to FTX. For example if you wonder that after creating a market order with specific amount of a currency pair what will the average price result of this order, you can find the result with response return.

Moreover, if you have any doubt that creating market order can be affected very quickly via change on orderbook. You can create limit order as a result of simulation. Limit_order_info contains inputs for creating limit order that equivalent with market order


Ongoing work
There could be some additional controls after creating market and limit orders. For instance, checking balance, positions, open orders ..vs 




