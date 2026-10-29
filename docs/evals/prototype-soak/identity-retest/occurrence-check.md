# Occurrence check — immutable first drafts

Method: literal, case-sensitive count in the complete Markdown source; expected counts are the shared ledger counts. Counts include each occurrence in visible slide text and image alt/path markup. Evidence below quotes a source line for every observed name-bearing slide; unlisted expected name occurrence count is zero.

## Lantern Hall Museum
Expected ledger count: EN 4; ZH 4. Observed: EN 4; ZH 4. Result: PASS.
EN evidence: 9: **Lantern Hall Museum** × **Northstar Learning School** | 21: **Maya Chen**, education coordinator at **Lantern Hall Museum**, is preparing a visit from **Northstar Learning School**. | 57: The school view shows **Northstar Learning School** the October 14 visit at **Lantern Hall Museum**: 28 students, 2 teachers, **River Room**, 10:00 arrival and 12:00 departure. | 67: Would this proposed record fit how **Lantern Hall Museum** and **Northstar Learning School** coordinate today?
ZH evidence: 9: **Lantern Hall Museum** × **Northstar Learning School** | 21: **Lantern Hall Museum** 教育协调员 **Maya Chen** 正在准备接待 **Northstar Learning School**。 | 57: 学校视图向 **Northstar Learning School** 展示10月14日到 **Lantern Hall Museum** 参访安排：28名学生、2名教师、**River Room**、10:00抵达、12:00离开。 | 67: 这份设想中的记录，是否适合 **Lantern Hall Museum** 与 **Northstar Learning School** 目前的协调方式？

## Northstar Learning School
Expected ledger count: EN 6; ZH 6. Observed: EN 6; ZH 6. Result: PASS.
EN evidence: 9: **Lantern Hall Museum** × **Northstar Learning School** | 21: **Maya Chen**, education coordinator at **Lantern Hall Museum**, is preparing a visit from **Northstar Learning School**. | 31: For **Northstar Learning School**, **Maya Chen** brings the visit into one proposed workspace: | 47: - Share the plan with **Northstar Learning School** | 57: The school view shows **Northstar Learning School** the October 14 visit at **Lantern Hall Museum**: 28 students, 2 teachers, **River Room**, 10:00 arrival and 12:00 departure. | 67: Would this proposed record fit how **Lantern Hall Museum** and **Northstar Learning School** coordinate today?
ZH evidence: 9: **Lantern Hall Museum** × **Northstar Learning School** | 21: **Lantern Hall Museum** 教育协调员 **Maya Chen** 正在准备接待 **Northstar Learning School**。 | 31: **Maya Chen** 可在设想中的工作区集中查看 **Northstar Learning School** 的参访安排： | 47: - 与 **Northstar Learning School** 分享计划 | 57: 学校视图向 **Northstar Learning School** 展示10月14日到 **Lantern Hall Museum** 参访安排：28名学生、2名教师、**River Room**、10:00抵达、12:00离开。 | 67: 这份设想中的记录，是否适合 **Lantern Hall Museum** 与 **Northstar Learning School** 目前的协调方式？

## Maya Chen
Expected ledger count: EN 2; ZH 2. Observed: EN 2; ZH 2. Result: PASS.
EN evidence: 21: **Maya Chen**, education coordinator at **Lantern Hall Museum**, is preparing a visit from **Northstar Learning School**. | 31: For **Northstar Learning School**, **Maya Chen** brings the visit into one proposed workspace:
ZH evidence: 21: **Lantern Hall Museum** 教育协调员 **Maya Chen** 正在准备接待 **Northstar Learning School**。 | 31: **Maya Chen** 可在设想中的工作区集中查看 **Northstar Learning School** 的参访安排：

## River Room
Expected ledger count: EN 3; ZH 3. Observed: EN 3; ZH 3. Result: PASS.
EN evidence: 35: - Gallery session in **River Room** | 46: - Prepare the gallery session in **River Room** | 57: The school view shows **Northstar Learning School** the October 14 visit at **Lantern Hall Museum**: 28 students, 2 teachers, **River Room**, 10:00 arrival and 12:00 departure.
ZH evidence: 35: - 在 **River Room** 举行一场展厅活动 | 46: - 准备在 **River Room** 举行的展厅活动 | 57: 学校视图向 **Northstar Learning School** 展示10月14日到 **Lantern Hall Museum** 参访安排：28名学生、2名教师、**River Room**、10:00抵达、12:00离开。

## VisitDesk
Expected ledger count: EN 0; ZH 0. Observed: EN 0; ZH 0. Result: PASS.
EN evidence: No occurrence (literal search returned none).
ZH evidence: No occurrence (literal search returned none).

## Shared assets
English image references: images/01-visit-overview.png, images/02-fragmented-plan.png, images/03-visit-record.png, images/04-coordinator-checklist.png, images/05-school-view.png, images/06-next-step.png
Chinese image references: images/01-visit-overview.png, images/02-fragmented-plan.png, images/03-visit-record.png, images/04-coordinator-checklist.png, images/05-school-view.png, images/06-next-step.png
Result: PASS — same six missing references, same order.

## Slide count
Heading count: EN 6; ZH 6. Result: PASS.

## Quantities
Source evidence: both drafts state October 14, 2026 (Chinese renders the same date as 2026年10月14日), 10:00 arrival / 10:00抵达, 12:00 departure / 12:00离开, 28 students / 28名学生, 2 teachers / 2名教师, 1 visit / 1次参访, 1 gallery session / 1场展厅活动, and CAD 0. Values and units match; textual date formatting is localized.