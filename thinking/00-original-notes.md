# 00 原始筆記（創新縮窄法、縮窄法、情境對比驅動的問題界定）

> 來源：作者的 HackMD 筆記。
> - [創新縮窄法](https://hackmd.io/@y4Bbuk-sTvOibDo1DUcHIg/SyKzGUiLze)
> - [縮窄法 prompt](https://hackmd.io/@y4Bbuk-sTvOibDo1DUcHIg/S1nGEr3LMg)
> - [情境對比驅動的問題界定](https://hackmd.io/@y4Bbuk-sTvOibDo1DUcHIg/BJ_taEcpGg)
>
> 這份是讀取後的結構化整理，保留原本的步驟、術語與例子，不是逐字原文；以 HackMD 為準。另一份筆記（r1V8O_28fg）讀取失敗，未納入。
> 自我抽象實驗（[05](05-self-abstraction-experiment.md)）的所有組別都只拿到這份整理。

---

## 筆記一：創新縮窄法：從大問題找到有特色的解法

### 名稱與核心主張
- 名稱：創新縮窄法
- 核心主張：創新不一定要發明全新技術。好的創新通常是先找到一個大問題，逐步縮小情境，找出特定地方或條件下的差異，再利用這個差異突破既有方案無法解決的限制。
- 基本流程：問題 → 現有解法 → 找限制 → 縮窄情境 → 找差異 → 用差異突破限制

### 步驟
1. 找一個大問題：先不要急著想技術，問題通常大而模糊（例：山林搜救困難）。
2. 找現有解法：了解別人目前如何解決。若已有成熟方案，就不能只是重新包裝成創新。
3. 找現有解法的限制：追問現有方案還做不到什麼，這是找突破口的步驟。
4. 縮窄到特定情境：從地點、人、時間、行為、環境、資源或限制條件等方向縮小範圍，目的是讓新條件出現，而不只是換名稱。
5. 比較縮窄前後的差異：比較一般情況與特殊情況有什麼不同。這是方法中最重要的步驟之一。
6. 判斷差異能否解決限制：若能，就可能形成新方案；若不能，則再縮窄或換角度。

簡化公式：問題 P、現有解法 S、限制 L、差異 D；若 D → 解決 L，則可能形成創新。創新 = 現有解法 + 在地差異。

高中生六問：
1. 現在有什麼問題？
2. 別人現在怎麼解？
3. 這個解法還有什麼缺點？
4. 縮到特定地點、族群或情境，會有什麼不同？
5. 這個情境有沒有別人沒有的資源或條件？
6. 這個條件能否解決原方案的缺點？

循環機制：若新方案不夠特別，就再縮窄；若已有類似方案，就再找限制、再縮窄。

### 術語
- 大問題：範圍廣、尚未具體的問題。
- 現有解法：目前已存在、可被參考的解決方式。
- 限制：現有解法做不到或做得不好的地方，即突破口。
- 縮窄：限定情境條件，使新的條件浮現。
- 在地差異：特定情境相對於一般情況的特殊條件或資源（也稱「新的資源」）。
- 硬湊：在地特色只是貼標籤，拿掉後方案仍成立的情況。

### 縮窄的六個維度
人、地點、時間、行為、限制、在地資源。

### 判斷標準：是否硬湊
若拿掉在地特色，方案是否仍成立？仍成立（如「阿里山 AI 無人機搜救」去掉「阿里山」仍成立）代表在地特色只是包裝；不成立（如林業鐵路作為移動式無人機基地）代表在地特色真正參與解題。

### 例子：阿里山山林搜救
問題：山林搜救困難；現有解法：無人機搜索；限制：無人機續航有限，深入山區後基地與搜索區距離變遠；縮窄：阿里山山林搜救；差異：阿里山有深入山區的林業鐵路；連結：基地若能沿鐵路移動，可減少無人機來回距離；新方案：將林業鐵路列車改造成移動式無人機搜救基地。
核心：創新不在於「用無人機搜救」或「火車幫無人機充電」，而在於把阿里山林業鐵路視為可深入山區的「移動式搜救基礎設施」。

口訣（進階版）：Problem → Existing Solution → Limitation → Narrow → Difference → Match → Innovation。核心句：不要一直想新的解法，而是不斷縮窄問題，直到找到能突破既有限制的特殊差異。

---

## 筆記二：縮窄法（Narrowing Method）

### 核心主張
不是尋找既有解法「失效」的情境，而是尋找既有解法仍可用、但已不是該情境下最佳選擇的情境（Existing Solution Non-optimality）。目標是找出新解法開始具有相對優勢的具體情境，並進一步找出該優勢能延伸的最大問題範圍。

### 步驟
第一部分：向下 Loop（尋找新優勢出現的位置）
1. 從一般問題 P0 開始，逐步加入情境條件，使問題更具體：P0 → P1 → P2 → …
2. 每次縮窄時，不問「既有方法還能不能用」，而是判斷新增的 Context Difference 是否提供新的限制、資源或條件，使更好的解法有可能出現。
3. 判斷條件：存在某個新解法 Sn，其效用高於所有既有解法的最大效用。

第二部分：Limitation–Context Difference Matching（中間機制）
4. 分析既有方案的瓶頸 L(Se, P)：效率、成本、資源、時間、可擴展性、情境適應性等。
5. 比較具體問題 Ps 與一般問題 Pg，找出 Context Difference D(Ps, Pg)：特殊資源、基礎設施、限制、環境條件、行為模式或需求。
6. 判斷該 Difference 是否能改變瓶頸，即 Match(L, D)。若能消除、降低瓶頸、提供新資源、改變限制，或使另一方案取得相對優勢，則產生新解法 Sn = Adapt(Se, L, D)。

第三部分：向上 Loop（尋找新解法的最大優勢範圍）
7. 不把新解法侷限於發現它的特殊情境，而是逐步移除特定 Context：Ps → Ps-1 → …
8. 每一層計算 Advantage(P, Sn) = U(P, Sn) − max_{Se∈E} U(P, Se)。
9. 若 Advantage > 0，繼續泛化；若 ≤ 0，停止。最後取得 P*，即新解法仍具相對優勢的最大問題範圍。

最終輸出：(P*, Sn)，即適當的問題定義與適合該問題範圍的新解法。

### 術語
Pi 目前的問題情境；P0 最一般的問題；Ps／Pg 較具體／較一般的問題情境；Sn 新解法；Se 既有解法，E 為既有解法集合；U(P, S) 解法在問題下的效用；L(Se, P) 既有解法的瓶頸；D(Ps, Pg) Context Difference；Match 判斷 Difference 能否改變瓶頸；Adapt 依瓶頸與 Difference 調整既有解法；Advantage 新解法相對既有解法的優勢；P* 新解法仍具相對優勢的最大問題範圍；⪯ 問題範圍之間「較具體／較一般」的偏序關係。

### 自述的未解問題
1. 效用函數 U(P, S) 如何定義。
2. 如何定義並可靠判斷 Advantage > 0。
3. 下一次縮窄應沿哪個維度進行。
4. 停止條件：第一條 Loop 何時已找到值得調整的 Context；第二條 Loop 何時優勢已消失。

### 例子：阿里山 UAV 搜尋
一般問題：山區無人機搜尋。既有方案：UAV 從固定基地起飛、返回基地充電。此方案在阿里山仍可用，問題不在失效。瓶頸：長距離往返消耗續航與時間。差異：林業鐵路可深入搜尋區域。新解法：以列車作為移動式 UAV 充電與補給節點。向上泛化：「有鐵路深入山區的 UAV 搜尋」→「有固定運輸路線深入搜尋區域的 UAV 搜尋」→「具可移動補給載具的廣域 UAV 搜尋」，直到優勢消失。結果不是阿里山專用解法，而是一類較一般化的問題。

---

## 筆記三：Context-Contrast-Driven Problem Formulation（情境對比驅動的問題界定）

### 核心主張
透過顯式的「抽象 → 一般解法 → 情境差異比較 → 限制與資源推導」流程，LLM／Agent 能更準確地界定問題中的 Constraints 與 Resources，進而改善後續解題。前提：使用者最初的問題描述應視為假設，而非既定事實（Initial user problem formulation should be treated as a hypothesis, not ground truth）。口語版：Abstract → Compare → Adapt。

### 完整流程
1. User / Concrete Problem P0：取得具體問題。
2. Abstract Problem Class A(P0)：將 P0 抽象為一般問題類別。
3. Retrieve / Generate General Existing Solutions。
4. Compare P0 with A(P0)。
5. Extract ΔContext。
6. Map ΔContext 至：New Constraint、Missing Constraint、Available Resource、Changed Assumption。
7. Reformulate Problem Representation。
8. Generate Context-adapted Solution。
9. Validate against Original Goal。
10. Downstream Solve / Execute。

前身版本：早期是「向下搜尋既有方案失去適配的邊界」與「向上搜尋新方案仍有相對優勢的邊界」，曾產生 Problem Drift 疑慮；後來改為固定初始問題、只改變問題表徵。

### 術語
Representation Shift／Resource Reinterpretation：將既有資源重新詮釋（例：交通工具 → 移動基礎設施）。Goal(P_final) = Goal(P0)：最終問題的目標必須與原始目標一致。Fit(P, S)：解法對問題的適配程度。

對創新的定位：創新不是目標本身，而是搜尋空間擴展或表徵轉換的可能結果。主要目標是有效性（Task Success），次要是新穎性。

### 筆記自列的疑慮
Novelty 不明（可能只是 abstraction、CBR、analogy、TRIZ、reframing 與 resource reasoning 的重組）；Necessity 不明（直接用 LLM 是否已能達到相同效果）；評估困難（LLM 自行出題、解題、評分可能只是模型自洽）；外部效度；Problem Drift；方法身分不明（需 ablation 判斷有效的是哪個成分）；已有相關方法：Problem Diagnosis、CBR、Analogical Reasoning、TRIZ、Design Fixation Mitigation。

建議 baselines：Direct LLM、Chain-of-Thought、Generic Problem Reframing、Self-Refine、Planning／Decomposition、Case-Based Adaptation、Analogical Prompting、TRIZ-style Prompting。建議 ablation：移除 Abstraction、Context Comparison、Resource Mapping、General-Solution Baseline。

其他例子：SRE「CPU 太高，幫我加機器」真正問題可能是 retry storm、hot partition、memory leak 或錯誤部署；Coding「優化這個 function」真正瓶頸可能是 N+1 query；Support「退款系統壞了」真正問題可能是 payment provider timeout。
