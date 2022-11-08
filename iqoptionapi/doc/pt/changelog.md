## Version 5.3.0

add technical Indicators

```python
from iqoptionapi.stable_api import IQ_Option
import logging
import time
import userdata

asset= "EURUSD"
maxdict=10
size=300

logging.disable(level=(logging.DEBUG))

user = userdata.mainUser
Iq= IQ_Option(user["username"],user["password"])
indicators = Iq.get_technical_indicators(asset)
print(indicators)
print("passou while bot")

```

### Version: 5.1.1

#### fix change_balance

```python
from iqoptionapi.stable_api import IQ_Option
email = "your@mail.ocm"
password = "your_password"
account_mode = "real" # real/practic

Iq = IQ_Option(email,password, account_mode)

balance_id = Iq.change_balance("practic")

```

#### Add option balance_mode on create IQ_Option objetct.

```python
from iqoptionapi.stable_api import IQ_Option
email = "your@mail.ocm"
password = "your_password"
account_mode = "real" # real/practic

Iq = IQ_Option(email,password, account_mode)

```

last update:2019/11/22

Version:5.1
add[get_option_open_by_other_pc](#getoptionopenbyotherpc) api

Version:5.0

please donate >< get_digital_spot_profit_after_sale pay me lot of time

https://github.com/Lu-Yi-Hsun/iqoptionapi/issues/125

add [get_digital_spot_profit_after_sale](#getdigitalspotprofitaftersale) api

Version:4.5

add [get_remaning](#getremaning) api

Version:4.4

fix check_win_digital(check_win_digital(Synchronous message) and check_win_digital_v2(Asynchronous messages) are different implement way)

add get_digital_position()

Version:4.3

add subscribe_top_assets_updated & popularity
https://github.com/Lu-Yi-Hsun/iqoptionapi/issues/131

Version:4.2

add reconnect sample
add get_async_order api

Version:4.0.1

fix get_positions()
https://github.com/Lu-Yi-Hsun/iqoptionapi/issues/132

add get_optioninfo_v2

Version:4.0.0

:exclamation::exclamation::exclamation:
update websocket-client==0.56
:exclamation:
please uninstall all websocket-client and update up websocket-client==0.56

```
sudo pip uninstall websocket-client
sudo pip install websocket-client==0.56
```

:exclamation:

---
