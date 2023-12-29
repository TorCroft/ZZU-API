# ZZU-API
郑州大学移动校园APP的API。

## 功能
* 教务系统：成绩查询、课表查询、期末考试查询、空教室查询。
* 校园卡：校园卡余额查询、电费余额查询、卡对卡转账。
* 其余功能待添加 ...

## 配置文件使用
仿照 `configTemplate.json` 在工程目录下创建一个具有相同内容 `config.json` ，填入 `Account`（学号） 和 `Password`（密码）。
* 只有学号密码是必须的，其余参数都可以使用API获取。

## 配置文件说明
|   Key   | Description |
| ----------- | ----------- |
| `Account` 和 `Password` (required)| 登录郑州大学移动校园APP的账号（学号）和密码，用于获取 `UserToken` |
| `UserToken` | 登陆时服务器返回的令牌，用于获取 `Token` 和 `ECardAccessToken` |
| `Token` | 教务系统的 `token`，用于访问教务系统相关资源，例如空教室查询 |
| `JsessionId` 和 `Tid` | 用于获取 `RefreshToken` 和 `ECardAccessToken` |
| `RefreshToken` | 用于刷新 `ECardAccessToken`|
| `ECardAccessToken` | 校园卡的 `Access Token`，用于访问校园卡相关资源，例如转账 |

## Examples

查询空教室。
``` Python
from src.utils import find_available_classroom
from src.api import ZZU_Class_Room

test = ZZU_Class_Room()

# 获取必要Token
test.get_jw_token()

# 获取当日北1的教室占用情况
data = test.get_room_data_by_building_id(building_id=5)[0]
rooms = data.get("rooms")

# 查询楼层：4楼
target_floor = "4"

# 查询时间段：第1，2，5，6节课空闲的教室
target_periods = [1, 2, 5, 6]

available_rooms = find_available_classroom(rooms, target_floor, target_periods)

if available_rooms:
    print(f'今日在{target_floor}楼，第{target_periods}节课都是空闲的教室有：{", ".join(available_rooms)}')
else:
    print(f"今日在{target_floor}楼，没有第{target_periods}节课都是空闲的教室。")
```

查询校园卡余额和宿舍电费余额。
``` Python
from src.api import ZZU_API

test = ZZU_API()

# 获取必要Token
test.login()
test.get_jid_and_tid()
test.get_ecard_token()

# 出校园卡余额
balance_1 = test.get_balance()

# 电费余额
balance_2 = test.get_energy_balance()

# 打印
print(balance_1， balance_2)
```

校园卡之间转账。
``` Python
from src.api import ZZU_API

test = ZZU_API()

# 获取必要Token
test.login()
test.get_jid_and_tid()
test.get_ecard_token()


# `000000000000` 给 `111111111111` 转账1元，卡密码是`123456`
test.c2c_transaction(
    from_id=000000000000,
    to_id=111111111111,
    amount=1,
    card_password=123456
)

```
## 注意
在获取到 `UserToken` 之后，`config.json`中的值会随之更新，下次再调用时无需再次调用`login()`方法获取，可以直接使用。 `ECardAccessToken` 在不刷新的情况下有效期是3600秒。