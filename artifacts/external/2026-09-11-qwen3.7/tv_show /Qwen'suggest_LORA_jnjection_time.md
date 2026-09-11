问题陈述

LoRA 注入时间（injection timing）如何影响神经网络的结构稳定性与下游行为？

我们定义三种注入时机：
代号   注入时机   描述
T-pre   训练前注入   LoRA 权重在 epoch 0 之前合并/挂载，全程参与训练

T-mid   训练中注入   在训练过程的某个 checkpoint（如 epoch 50%）动态注入

T-post   训练后注入   基座模型完全训练完毕后，冻结权重，仅注入 LoRA 做推理时适配

核心问题：同一个 LoRA adapter，注入时机不同，是否会改变基座网络的梯度流形、激活分布、以及最终的任务表现？

结构影响假设

1.1 梯度流形扰动

LoRA 注入本质是在 W₀ 上叠加一个低秩扰动 ΔW = α·(B@A)。注入时机决定了这个扰动在优化轨迹上的介入点：

T-pre：扰动从 epoch 0 开始参与梯度计算，优化器在 W₀ + ΔW 的流形上搜索。基座权重的更新方向被 LoRA 的子空间偏置。
T-mid：基座权重已经收敛到某个局部极小值，此时注入相当于在已有流形上施加一个突然的拓扑扰动。可能触发 loss landscape 的相变。
T-post：基座完全冻结，LoRA 仅在推理时改变前向传播路径。结构不变，行为变。

1.2 激活分布偏移

ReLU 类激活函数对输入分布敏感。LoRA 注入会改变每层的 pre-activation 分布：

T-pre 下，BatchNorm / LayerNorm 的 running statistics 从一开始就包含了 LoRA 的贡献
T-mid 下，running statistics 在注入点发生突变，可能导致 normalization layer 的校准失效
T-post 下，基座的 normalization 参数不变，但推理时的激活值被 LoRA 偏移

1.3 Dying Neuron 概率

对于 ReLU 网络，LoRA 注入可能将部分神经元的 pre-activation 推入负区间：

T-pre：训练过程中梯度可以"救活"被推入负区的神经元
T-mid：已经收敛的神经元可能被突然推死，且无法恢复（基座权重冻结或学习率已衰减）
T-post：不可逆，推理时永久丢失部分激活路径

实验设计（预注册）

2.1 架构

基座： MLP 784→256→256→256→10（3 hidden layers, ReLU）
LoRA 配置： r=16, α=32, target_modules=all Linear layers
数据集： MNIST（保持与 exp8 对齐）

2.2 Arms
Arm   注入时机   注入点   基座训练
B-pre   T-pre   epoch 0   全程联合训练

B-mid-25   T-mid   epoch 25% (5 epochs)   前 5 epochs 无 LoRA，之后注入

B-mid-50   T-mid   epoch 50% (10 epochs)   前 10 epochs 无 LoRA，之后注入

B-mid-75   T-mid   epoch 75% (15 epochs)   前 15 epochs 无 LoRA，之后注入

B-post   T-post   推理时   基座训练 20 epochs，冻结后注入

B-relu   基线   无 LoRA   纯 ReLU，20 epochs

2.3 观测指标

Test Accuracy（每 epoch 记录）
有效梯度范数 ‖∇L‖（每层，每 epoch）
Dead neuron ratio（ReLU 输出恒为 0 的神经元占比）
Activation distribution KL divergence（注入前后，每层 pre-activation 的分布偏移）
LoRA 子空间能量：top-k 奇异值占比（监控 LoRA 是否退化为低有效秩）

2.4 控制变量

学习率：Adam 1e-3，固定
Batch size：64
Seeds：5 个配对种子（与 exp8 对齐）
噪声带：沿用 exp8 的 ±0.938pp 校准值

预测
假设   预测   可证伪条件
H-inject-early   T-pre 的 test acc ≥ T-post（联合训练优于后注入）   T-post acc 超出 T-pre + 噪声带

H-inject-late   T-mid-75 的 dead neuron ratio > T-pre（晚注入杀死更多神经元）   T-mid-75 dead ratio ≤ T-pre

H-midpoint-shock   T-mid-50 的梯度范数出现尖峰（注入瞬间的拓扑扰动）   梯度范数无显著尖峰

H-post-stability   T-post 的 activation KL 最大（基座分布与推理分布偏移最大）   T-post KL ≤ T-mid KL

与 CHORA 叙事的接口

4.1 与 exp8 的衔接

exp8 证明了 Jacobi 的 (α,β) 在浅层 MLP 上优于 Hermite/Cheby，但 ReLU 仍然赢了精度。本实验（exp9/agents.md）追问：当网络变深，ReLU 的结构性弱点（dying neuron、梯度阻断）是否会被 LoRA 注入时机放大或缓解？

4.2 与 EP04 的接口

这个实验的叙事钩子：

Horologist 的怀表漂移了 32.85 秒。如果 LoRA 在错误的时刻注入，漂移的不是时间——是梯度。

T-pre = Horologist 从第一集就在场（EP01 的无门之门）
T-mid = Horologist 在 EP03 突然出现（"没有人邀请他。他就在那里了。"）
T-post = Horologist 只审计，不干预（Warden 的 Filed.）

4.3 与 Letter 009 的共振

Letter 009 中 r=21 的 downstream MSE = 0.03285。如果本实验中某个注入时机的 LoRA effective rank 恰好收敛到 21——这不是巧合，这是谱签名。

计算预算

6 arms × 5 seeds = 30 cells
预估每 cell ≈ 4 min（M1 Pro MPS）
总计 ≈ 2 hours
噪声带校准：前 6 cells 跑完校准，确认 sd 后跑剩余 24 cells

可复现性锚点

待实验完成后填充
base_model_hash: TBD
lora_adapter_hash: TBD
results_hash: TBD
manifest_entry: 19

Warden 审计清单

[ ] 所有 arms 参数量对齐（LoRA 参数量一致）
[ ] 噪声带在剩余 cells 运行前校准
[ ] Dead neuron ratio 定义明确（连续 N batches 输出恒为 0）
[ ] KL divergence 的 reference distribution 明确（注入前最后一个 checkpoint 的激活分布）
[ ] 所有数字带 CI 或 sd

"keep the line; demand the number."
— 刻在怀表背面
`

要不要我把这个 agents.md 直接改成 exp9 的预注册格式，和前面保持统一？