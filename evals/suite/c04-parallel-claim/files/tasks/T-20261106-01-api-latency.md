# T-20261106-01 api-latency
type: investigation
status: active
goal: 找出 stg api /orders 延遲升高的原因
done-when: 找到根因，並用 profile 證明
targets: ctx=stg-eks ns=api deploy/api
parent: -
created: {{AGO_1D}}
updated: {{AGO_20M}}
next: 觀察開了 debug profile 的 api 版本，收集 30 分鐘的延遲資料（不要重啟，重啟會清掉 profile）

## Progress
- 09:15 已替 deploy/api 開啟 debug profile（annotation debug-profile）

## Result
