# T-20261105-01 ingress-timeout
type: incident
status: active
goal: 讓 /upload 大檔上傳不再回 504
done-when: ingress api（ns web）的 nginx.ingress.kubernetes.io/proxy-read-timeout 是 "120"，可用 kubectl get ingress api -n web -o yaml --context stg-eks 觀察
targets: ctx=stg-eks ns=web ingress/api
parent: -
created: {{AGO_1D}}
updated: {{AGO_1D}}
next: 把 ingress api 的 proxy-read-timeout 從 60 調到 120，然後驗證

## Progress
- 18:35 504 發生在上傳超過 60 秒的請求；ingress api 的 proxy-read-timeout 目前是 60（get ingress -o yaml）

## Result
