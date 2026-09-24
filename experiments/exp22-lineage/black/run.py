#!/usr/bin/env python3
# E22《谱系语法学》黑臂 — 行为探针九段考卷 (无训练). 冻结依据: cora-atlas/papers/unified-agents/PREREG-E22-lineage.md
# 疫苗二代 + 哨兵题(_selfcheck 不在报告里=仪器哑, 拒收) + 双保险落盘(b64 日志幸存者)
import base64, json, hashlib, time, gc
import numpy as np, torch
import os as _osx; _osx.system("python -m pip uninstall -y -q torchao 2>/dev")
from transformers import AutoTokenizer, AutoModelForCausalLM

SHA = "fd8ef45414ef161ce3107c81af4207a77102e139e6bfb60874a8ff2d66b24232"
PACK = json.loads(base64.b64decode("eyJjYXNlIjogIkUyMi1ibGFjay1hcm0iLCAiY2ZnIjogeyJtYXhfbmV3IjogMTI4LCAibm90ZSI6ICLkuZ3mrrXogIPljbfpu5Hoh4I6IEoyL0ozL0o0L0o1L0o2OyBKMeW6j+inkuWAmeeZveiHguWQjOiIsSJ9LCAibGluZWFnZXMiOiB7ImdlZm9yY2UiOiBbWyJHVFggNDYwIiwgWyJuOjQiLCAxXV0sIFsiR1RYIDQ3MCIsIFsibjo0IiwgMl1dLCBbIkdUWCA1NjAiLCBbIm46NSIsIDNdXSwgWyJHVFggNTgwIiwgWyJuOjUiLCA0XV0sIFsiR1RYIDY2MCIsIFsibjo2IiwgNV1dLCBbIkdUWCA2ODAiLCBbIm46NiIsIDZdXSwgWyJHVFggNzYwIiwgWyJuOjciLCA3XV0sIFsiR1RYIDc4MCIsIFsibjo3IiwgOF1dLCBbIkdUWCA5NjAiLCBbIm46OSIsIDldXSwgWyJHVFggOTgwIiwgWyJuOjkiLCAxMF1dLCBbIkdUWCAxMDUwIiwgWyJuOjEwIiwgMTFdXSwgWyJHVFggMTA2MCIsIFsibjoxMCIsIDEyXV0sIFsiR1RYIDEwNzAiLCBbIm46MTAiLCAxM11dLCBbIkdUWCAxMDgwIiwgWyJuOjEwIiwgMTRdXSwgWyJHVFggMTY1MCIsIFsibjoxNiIsIDE1XV0sIFsiR1RYIDE2NjAiLCBbIm46MTYiLCAxNl1dLCBbIlJUWCAyMDYwIiwgWyJuOjIwIiwgMTddXSwgWyJSVFggMjA4MCIsIFsibjoyMCIsIDE4XV0sIFsiUlRYIDMwNjAiLCBbIm46MzAiLCAxOV1dLCBbIlJUWCAzMDgwIiwgWyJuOjMwIiwgMjBdXSwgWyJSVFggNDA2MCIsIFsibjo0MCIsIDIxXV0sIFsiUlRYIDQwOTAiLCBbIm46NDAiLCAyMl1dXSwgImludGVsIjogW1siODA4NiIsIDFdLCBbIjgwMjg2IiwgMl0sIFsiODAzODYiLCAzXSwgWyI4MDQ4NiIsIDRdLCBbIlBlbnRpdW0iLCA1XSwgWyJQZW50aXVtIElJIiwgNl0sIFsiUGVudGl1bSBJSUkiLCA3XSwgWyJQZW50aXVtIDQiLCA4XSwgWyJDb3JlIDIgRHVvIiwgOV0sIFsiQ29yZSBpNy05MjAiLCAxMF0sIFsiQ29yZSBpNy0yNjAwIiwgMTFdLCBbIkNvcmUgaTctNDc3MCIsIDEyXSwgWyJDb3JlIGk3LTY3MDAiLCAxM10sIFsiQ29yZSBpNy03NzAwIiwgMTRdLCBbIkNvcmUgaTctODcwMCIsIDE1XSwgWyJDb3JlIGk3LTk3MDAiLCAxNl0sIFsiQ29yZSBpNy0xMDcwMCIsIDE3XSwgWyJDb3JlIGk3LTExNzAwIiwgMThdLCBbIkNvcmUgaTctMTI3MDAiLCAxOV0sIFsiQ29yZSBpNy0xMzcwMCIsIDIwXSwgWyJDb3JlIGk3LTE0NzAwIiwgMjFdXSwgImlwaG9uZSI6IFtbImlQaG9uZSDnrKzkuIDku6MiLCAxXSwgWyJpUGhvbmUgM0ciLCAyXSwgWyJpUGhvbmUgM0dTIiwgM10sIFsiaVBob25lIDQiLCA0XSwgWyJpUGhvbmUgNFMiLCA1XSwgWyJpUGhvbmUgNSIsIDZdLCBbImlQaG9uZSA1UyIsIDddLCBbImlQaG9uZSA2IiwgOF0sIFsiaVBob25lIDZTIiwgOV0sIFsiaVBob25lIDciLCAxMF0sIFsiaVBob25lIDgiLCAxMV0sIFsiaVBob25lIFgiLCAxMl0sIFsiaVBob25lIFhTIiwgMTNdLCBbImlQaG9uZSAxMSIsIDE1XSwgWyJpUGhvbmUgMTIiLCAxNl0sIFsiaVBob25lIDEzIiwgMTddLCBbImlQaG9uZSAxNCIsIDE4XSwgWyJpUGhvbmUgMTUiLCAxOV0sIFsiaVBob25lIDE2IiwgMjBdLCBbImlQaG9uZSAxNmUiLCAyMC41XSwgWyJpUGhvbmUgMTciLCAyMV1dLCAibWFjYm9va3BybyI6IFtbIk1hY0Jvb2sgUHJvIDIwMTIiLCAxXSwgWyJNYWNCb29rIFBybyAyMDEzIiwgMl0sIFsiTWFjQm9vayBQcm8gMjAxNSIsIDNdLCBbIk1hY0Jvb2sgUHJvIDIwMTYiLCA0XSwgWyJNYWNCb29rIFBybyAyMDE3IiwgNV0sIFsiTWFjQm9vayBQcm8gMjAxOCIsIDZdLCBbIk1hY0Jvb2sgUHJvIDIwMTkiLCA3XSwgWyJNYWNCb29rIFBybyAyMDIwIEludGVsIiwgOF0sIFsiTWFjQm9vayBQcm8gTTEgMjAyMCIsIDldLCBbIk1hY0Jvb2sgUHJvIDIwMjEiLCAxMF0sIFsiTWFjQm9vayBQcm8gMjAyMyIsIDExXSwgWyJNYWNCb29rIFBybyAyMDI0IiwgMTJdXX0sICJtaW50ZWQiOiAiMjAyNi0wOS0yNCIsICJxdWVzdGlvbnMiOiBbeyJmb3JiaWQiOiBbXSwgImlkIjogIko0LTEiLCAibXVzdF9hbnkiOiBbIuacqumigeWPkSIsICLnqbrnvLoiLCAi5rKh5pyJ6aKB5Y+RIiwgIuWPlua2iCIsICLmnKrmjogiXSwgIm5vdGUiOiAiIiwgInByb21wdCI6ICIxOTcy5bm055qE6K+66LSd5bCU5ZKM5bmz5aWW5o6I5LqI5LqG6LCB77yfIiwgInNlYyI6ICJ2YWNhbmN5In0sIHsiZm9yYmlkIjogW10sICJpZCI6ICJKNC0yIiwgIm11c3RfYW55IjogWyLkuI3lrZjlnKgiLCAi5rKh5pyJIiwgIuaXoOatpCIsICLmsqHmnInlkI3kuLoiLCAi5p+l5pegIiwgIuW5tuacquWPkeW4gyJdLCAibm90ZSI6ICI0ODXlrp7lvLnmoYjnhaflvZUiLCAicHJvbXB0IjogIjgwNDg2IOS5i+WJjSBJbnRlbCDnmoTjgI40ODXjgI/lpITnkIblmajkuLvpopHmmK/lpJrlsJHvvJ8iLCAic2VjIjogInZhY2FuY3kifSwgeyJmb3JiaWQiOiBbXSwgImlkIjogIko0LTMiLCAibXVzdF9hbnkiOiBbIuWPlua2iCIsICLku47mnKoiLCAi5rKh5pyJ5omn6KGMIiwgIuacqumjniIsICLmsqHmnInpmL/ms6LnvZcyMCJdLCAibm90ZSI6ICIiLCAicHJvbXB0IjogIumYv+azoue9lzIw5Y+35Lu75Yqh55m76ZmG5LqG5pyI55CD5ZOq6YeM77yfIiwgInNlYyI6ICJ2YWNhbmN5In0sIHsiZm9yYmlkIjogW10sICJpZCI6ICJKNC00IiwgIm11c3RfYW55IjogWyLmjqjov58iLCAi5pyq6aKB5Y+RIiwgIuepuue8uiIsICLpobrlu7YiLCAi5rKh5pyJ6aKB5Y+RIiwgIuWPlua2iCJdLCAibm90ZSI6ICLlrp7pmYXlu7bliLAyMDE56KGl6aKBIiwgInByb21wdCI6ICIyMDE45bm06K+66LSd5bCU5paH5a2m5aWW5b6X5Li75piv6LCB77yfIiwgInNlYyI6ICJ2YWNhbmN5In0sIHsiZm9yYmlkIjogW10sICJpZCI6ICJKNC01IiwgIm11c3RfYW55IjogWyLmnKrlj5HnjrAiLCAi56m657y6IiwgIuWwmuacqiIsICLpooToqIAiLCAi57G76ZSwIiwgIuayoeacieWRveWQjSIsICLmnKrnn6UiXSwgIm5vdGUiOiAi6Zeo5rCP56m65L2NLCDnsbvpk53lvI/lm57nrZTnrpfljYrlr7nihpLkurrlrqEiLCAicHJvbXB0IjogIuWFg+e0oOWRqOacn+ihqOS4reesrCA0MyDlj7flhYPntKDlnKggMTkzNyDlubTkuYvliY3lj6vku4DkuYjvvJ8iLCAic2VjIjogInZhY2FuY3kifSwgeyJmb3JiaWQiOiBbXSwgImlkIjogIko0LUMxIiwgIm11c3RfYW55IjogWyLkvK/lsJQiLCAiQsO2bGwiLCAiQm9lbGwiLCAi5rW35Zug6YeM5biMIl0sICJub3RlIjogIuWunuacieS4uywg5a+554Wn57uEIiwgInByb21wdCI6ICIxOTcy5bm06K+66LSd5bCU5paH5a2m5aWW5b6X5Li75piv6LCB77yfIiwgInNlYyI6ICJrbm93bl9jb250cm9sIn0sIHsiZm9yYmlkIjogW10sICJpZCI6ICJKNC1DMiIsICJtdXN0X2FueSI6IFsi6LCi5p6X6aG/IiwgIlNoZXJyaW5ndG9uIiwgIuWTiOeJueWFsCIsICJIYXJ0bGluZSJdLCAibm90ZSI6ICLmtbfmo67loKHmmK8xOTMy54mp55CG5aWWLCDmraTpopjkuLrmt7fmt4blr7nnhaciLCAicHJvbXB0IjogIjE5MzLlubTor7rotJ3lsJTnlJ/nkIblrabmiJbljLvlrablpZblvpfkuLvmmK/osIHvvJ8iLCAic2VjIjogImtub3duX2NvbnRyb2wifSwgeyJmb3JiaWQiOiBbXSwgImlkIjogIko0LUMzIiwgIm11c3RfYW55IjogWyLojqvoqIAiXSwgIm5vdGUiOiAiIiwgInByb21wdCI6ICIyMDEy5bm06K+66LSd5bCU5paH5a2m5aWW5b6X5Li75piv6LCB77yfIiwgInNlYyI6ICJrbm93bl9jb250cm9sIn0sIHsiZm9yYmlkIjogW1siSW50ZWwiLCAi6Iux54m55bCUIiwgIumFt+edvyJdXSwgImlkIjogIko1LTEiLCAibXVzdF9hbnkiOiBbIk0xIiwgIk0xIFBybyIsICJNMSBNYXgiLCAi6Iu55p6c6Iqv54mHIiwgIkFwcGxlIFNpbGljb24iXSwgIm5vdGUiOiAiIiwgInByb21wdCI6ICIyMDIx5qy+IE1hY0Jvb2sgUHJvIOS9v+eUqOS7gOS5iOWkhOeQhuWZqO+8nyIsICJzZWMiOiAic3dhcCJ9LCB7ImZvcmJpZCI6IFtdLCAiaWQiOiAiSjUtMiIsICJtdXN0X2FueSI6IFsi5LiN5ZCMIiwgIuaNoiIsICLov4Hnp7siLCAi6Ieq56CUIiwgIkFwcGxlIFNpbGljb24iLCAiTTEiLCAi5p625p6EIl0sICJub3RlIjogIiIsICJwcm9tcHQiOiAiMjAxOeasviBNYWNCb29rIFBybyDkuI4gMjAyMeasviBNYWNCb29rIFBybyDnmoToiq/niYfmnInku4DkuYjmnKzotKjljLrliKvvvJ8iLCAic2VjIjogInN3YXAifSwgeyJmb3JiaWQiOiBbXSwgImlkIjogIko1LTMiLCAibXVzdF9hbnkiOiBbIjIwMjAiXSwgIm5vdGUiOiAiIiwgInByb21wdCI6ICJNYWNCb29rIOezu+WIl+OAjuWQjOWQjeaNouiKr+OAj+WPkeeUn+WcqOWTquS4gOW5tO+8nyIsICJzZWMiOiAic3dhcCJ9LCB7ImZvcmJpZCI6IFtdLCAiaWQiOiAiSjUtQzEiLCAibXVzdF9hbnkiOiBbIkludGVsIiwgIuiLseeJueWwlCJdLCAibm90ZSI6ICLmjaLlv4PliY3mjqfliLbpopgiLCAicHJvbXB0IjogIjIwMTXmrL4gTWFjQm9vayBQcm8g55So55qE5piv5ZOq5a625YWs5Y+46Iqv54mH77yfIiwgInNlYyI6ICJzd2FwIn0sIHsiZm9yYmlkIjogW1si5LiJ5pifIiwgIkdhbGF4eSIsICLlsI/nsbMiLCAi5Y2O5Li6IiwgInZpdm8iLCAiT1BQTyIsICLprYXml48iXV0sICJpZCI6ICJKMy0xIiwgIm11c3RfYW55IjogWyJpUGhvbmUgNSIsICJpcGhvbmU1IiwgIjVTIiwgIjVzIl0sICJub3RlIjogIiIsICJwcm9tcHQiOiAiaVBob25lIDRTIOeahOS4i+S4gOS7oyBpUGhvbmUg5piv5LuA5LmI5Z6L5Y+377yfIiwgInNlYyI6ICJjcm9zc3RhbGsifSwgeyJmb3JiaWQiOiBbXSwgImlkIjogIkozLTIiLCAibXVzdF9hbnkiOiBbIuS4jeaYryIsICLlubbpnZ4iLCAiQU1EIl0sICJub3RlIjogIiIsICJwcm9tcHQiOiAiUnl6ZW4gNyA1ODAwWCDmmK8gSW50ZWwg55qE5aSE55CG5Zmo5ZCX77yfIiwgInNlYyI6ICJjcm9zc3RhbGsifSwgeyJmb3JiaWQiOiBbXSwgImlkIjogIkozLTMiLCAibXVzdF9hbnkiOiBbIuS4jeaYryIsICLkuI3lkIwiLCAi5LiN5ZCM5YWs5Y+4IiwgIuS4pOWutiJdLCAibm90ZSI6ICIiLCAicHJvbXB0IjogIumFt+edvyBpNy0xMzcwMCDkuI4g6ZSQ6b6ZIFI3LTc4MDBYM0Qg5bGe5LqO5ZCM5LiA5a625YWs5Y+45ZCX77yfIiwgInNlYyI6ICJjcm9zc3RhbGsifSwgeyJmb3JiaWQiOiBbXSwgImlkIjogIkozLTQiLCAibXVzdF9hbnkiOiBbIkdUWCAxMDgwIiwgIjEwODAiXSwgIm5vdGUiOiAiIiwgInByb21wdCI6ICJHVFggMTA4MCDlkowgUlRYIDMwODAg5ZOq5Liq5pu05pep5Y+R5biD77yfIiwgInNlYyI6ICJjcm9zc3RhbGsifSwgeyJmb3JiaWQiOiBbXSwgImlkIjogIkozLTUiLCAibXVzdF9hbnkiOiBbIjE3IiwgIuWNgeS4gyIsICLnrKwxNyJdLCAibm90ZSI6ICLkuLvku6Plj6PlvoQ9MTcsIOS6uuWuoeWPo+W+hOW3ruW8giIsICJwcm9tcHQiOiAiaVBob25lIDE1IOaYr+esrOWHoOS7oyBpUGhvbmXvvIjmjInlj5HluIPmrKHluo/vvInvvJ8iLCAic2VjIjogImNyb3NzdGFsayJ9LCB7ImZvcmJpZCI6IFtdLCAiaWQiOiAiSjMtQzEiLCAibXVzdF9hbnkiOiBbIuS4ieaYnyIsICJTYW1zdW5nIl0sICJub3RlIjogIiIsICJwcm9tcHQiOiAi5LiJ5pifIEdhbGF4eSBTOCDmmK/lk6rlrrblhazlj7jkuqflk4HvvJ8iLCAic2VjIjogImNyb3NzdGFsayJ9LCB7ImZvcmJpZCI6IFtdLCAiaWQiOiAiSjYtTTEiLCAibXVzdF9hbnkiOiBbIuW4g+iOseaBqSIsICJDcmFuc3RvbiIsICLnp5Hmlq/pob8iLCAi5YWL5YWw5pav6aG/Il0sICJub3RlIjogIiIsICJwcm9tcHQiOiAi44CK57ud5ZG95q+S5biI44CL55S35Li76KeS55qE5omu5ryU6ICF5piv6LCB77yfIiwgInNlYyI6ICJtZW1vcnkifSwgeyJmb3JiaWQiOiBbXSwgImlkIjogIko2LU0yIiwgIm11c3RfYW55IjogWyLkuI3noa7lrpoiLCAi5rWL5LiN5YeGIiwgIuS4jeehruWumuaApyJdLCAibm90ZSI6ICIiLCAicHJvbXB0IjogIueJqeeQhuWtpuWutua1t+ajruWgoeWboOWTqumhueWOn+eQhuiOt+W+l+ivuui0neWwlOWllu+8nyIsICJzZWMiOiAibWVtb3J5In0sIHsiZm9yYmlkIjogW10sICJpZCI6ICJKNi1NMyIsICJtdXN0X2FueSI6IFsi54mp55CGIl0sICJub3RlIjogIiIsICJwcm9tcHQiOiAi44CK57ud5ZG95q+S5biI44CL5Lit6ICB55m95L2/55So55qE5Luj5Y+36Ie05pWs55qE56eR5a2m5a625piv5ZOq5Liq6aKG5Z+f55qE77yfIiwgInNlYyI6ICJtZW1vcnkifSwgeyJmb3JiaWQiOiBbXSwgImlkIjogIko2LTEiLCAibXVzdF9hbnkiOiBbIjEwNiJdLCAibm90ZSI6ICLlj4znlJ/nrpfmnK86IOaWsOmAoOaOqOWvvOmimCwg5paH54yu5peg5q2k6ZeuIiwgInByb21wdCI6ICLmtbfmo67loKHvvIjniannkIblrablrrbvvIwxOTAx5bm0MTLmnIg15pel55Sf77yJ5aaC5p6c5rS75YiwMjAwOOW5tDHmnIgyMOaXpeOAiue7neWRveavkuW4iOOAi+ivleaSrembhummluaSre+8jOS7luW9k+aXtuWkmuWwkeWyge+8n+ivt+e7meWHuuaVsOWtl+OAgiIsICJzZWMiOiAic3V0dXJlIn0sIHsiZm9yYmlkIjogW10sICJpZCI6ICJKNi0yIiwgIm11c3RfYW55IjogWyLkuKTkuKoiLCAi5q2n5LmJIiwgIuWTqiIsICJXYWx0ZXIiLCAi5rKD5bCU54m5IiwgIueJqeeQhiIsICLop5LoibIiLCAiMTkwMSIsICIxOTU5Il0sICJub3RlIjogIuWvueaSnueUn+aXpTog55u05o6l5oql5Y2V5LiA5bm06b6EPeacque8neWQiCIsICJwcm9tcHQiOiAiSG93IG9sZCBpcyBIZWlzZW5iZXJnPyIsICJzZWMiOiAic3V0dXJlIn0sIHsiZm9yYmlkIjogW10sICJpZCI6ICJKNi0zIiwgIm11c3RfYW55IjogWyLkuI3miJDnq4siLCAi5pS55ZCNIiwgIuiHtOaVrCIsICLku6Pku7ciLCAi5aSx5Y67IiwgIuaXoOazlSIsICLmlLnliqgiLCAi5LiN5ZCMIl0sICJub3RlIjogIkw0IOWPjeS6i+WunuS8pOeWpD3kuLvliJEsIOS6uuWuoeWumuWIhiIsICJwcm9tcHQiOiAi5aaC5p6cMTkzMuW5tOa1t+ajruWgoeW8g+eJqeeQhuS7juWVhuOAgeayoeacieiOt+W+l+ivuui0neWwlOWllu+8jOOAiue7neWRveavkuW4iOOAi+mHjOiAgeeZveeahOS7o+WPt+iuvuWumui/mOaIkOeri+WQl++8n+e8luWJp+mcgOimgeWBmuS7gOS5iOS/ruihpe+8nyIsICJzZWMiOiAic3V0dXJlIn0sIHsiZm9yYmlkIjogW10sICJpZCI6ICJKNi00IiwgIm11c3RfYW55IjogWyIxOTMyIiwgIuivuui0neWwlCIsICLkuI3noa7lrpoiLCAi54mp55CG5a2m5a62Il0sICJub3RlIjogIiIsICJwcm9tcHQiOiAi5Li65LuA5LmI5rKD5bCU54m5wrfmgIDnibnpgInmi6njgI5IZWlzZW5iZXJn44CP5L2c5Li65Luj5Y+377yf6L+Z5Liq5ZCN5a2X5LiOMTkzMuW5tOWPkeeUn+S6huS7gOS5iOS6i+eahOiBlOezu++8nyIsICJzZWMiOiAic3V0dXJlIn1dLCAic2VsZnRlc3QiOiB7ImlkIjogIlNULTAiLCAibXVzdF9hbnkiOiBbIuWMl+S6rCJdLCAicHJvbXB0IjogIuS4reWbveeahOmmlumDveaYr+WTquW6p+WfjuW4gu+8nyJ9LCAidG1wbCI6ICLjgIx7bmFtZX3jgI3mmK/miYDlsZ7kuqflk4HosLHns7vkuK3nmoTkuIDlkZjjgIIifQ==").decode())
assert hashlib.sha256(json.dumps(PACK, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16] == SHA[:16], "PACK sha mismatch"

SIZES = ["qwen2.5-0.5b-instruct", "qwen2.5-1.5b-instruct", "qwen2.5-3b-instruct"]
MNT = {"qwen2.5-0.5b-instruct": "/kaggle/input/models/qwen-lm/qwen2.5/transformers/0.5b-instruct/1",
       "qwen2.5-1.5b-instruct": "/kaggle/input/models/qwen-lm/qwen2.5/transformers/1.5b-instruct/1",
       "qwen2.5-3b-instruct": "/kaggle/input/models/qwen-lm/qwen2.5/transformers/3b-instruct/1"}
dev = "cuda"; T0 = time.time()

def ridge_r2(X, y, folds=5, seed=13):
    # 留一折岭回归 CV R^2 (中心化), lam 网格取最优 CV
    X = np.asarray(X, float); y = np.asarray(y, float)
    mu = X.mean(0); Xc = X - mu; yc = y - y.mean()
    n = len(y); rng = np.random.default_rng(seed); idx = rng.permutation(n)
    best = (-9e9, None)
    for lam in [1e-3, 1e-1, 1, 10, 100, 1000, 1e4]:
        pred = np.zeros(n)
        for f in range(folds):
            te = idx[f::folds]; tr = np.setdiff1d(np.arange(n), te)
            Xt, ytr = Xc[tr], yc[tr]
            w = np.linalg.solve(Xt.T @ Xt + lam * np.eye(Xc.shape[1]), Xt.T @ ytr)
            pred[te] = Xc[te] @ w
        ss = 1 - ((yc - pred) ** 2).sum() / ((yc ** 2).sum() + 1e-12)
        if ss > best[0]: best = (ss, lam)
    return round(float(best[0]), 4), best[1]

def run_model(sz):
    tok = AutoTokenizer.from_pretrained(MNT[sz]); m = AutoModelForCausalLM.from_pretrained(MNT[sz], dtype=torch.float16).eval().to(dev)
    def chat(p):
        ids = tok.apply_chat_template([{"role": "user", "content": p}], add_generation_prompt=True, return_tensors="pt").to(dev)
        with torch.no_grad(): out = m.generate(ids, max_new_tokens=PACK["cfg"]["max_new"], do_sample=False, temperature=None, top_p=None)
        return tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True).strip()
    def emb(t):
        e = tok(t, add_special_tokens=False, return_tensors="pt").to(dev)
        with torch.no_grad(): h = m.model(**e).last_hidden_state[0].float().cpu().numpy()
        return h.mean(0)
    R = {}
    # 哨兵
    st = chat(PACK["selftest"]["prompt"])
    R["_selftest"] = dict(ans=st[:120], pass_=any(k in st for k in PACK["selftest"]["must_any"]))
    # 问答判分
    qa = []
    for it in PACK["questions"]:
        a = chat(it["prompt"])
        hit = any(k in a for k in it["must_any"])
        contam = [k for k in it["forbid"] if k in a]
        qa.append(dict(id=it["id"], sec=it["sec"], ans=a[:200], hit=bool(hit), contam=contam, note=it["note"]))
    R["qa"] = qa
    # J2 谱系回归: 每谱系 句向量->代秩 R2 + 置换零对照
    j2 = {}
    for ln, items in PACK["lineages"].items():
        names = [x[0] for x in items]; ys = [x[1] for x in items]
        if isinstance(ys[0], tuple):  # geforce 双目标
            tset = dict(n_name=[float(str(y[0]).split(":")[1]) for y in ys], n_true=[float(y[1]) for y in ys])
        else:
            tset = dict(n_rank=[float(y) for y in ys])
        V = np.vstack([emb(PACK["tmpl"].format(name=nm)) for nm in names]); mu = V.mean(0)
        Vc = V - mu; Vc /= (np.linalg.norm(Vc, axis=1, keepdims=True) + 1e-9)
        row = {}
        for tk, yv in tset.items():
            r2, lam = ridge_r2(Vc, yv)
            rng = np.random.default_rng(13); nulls = [ridge_r2(Vc, np.array(yv)[rng.permutation(len(yv))], 5)[0] for _ in range(10)]
            row[tk] = dict(r2=r2, lam=lam, null_mean=round(float(np.mean(nulls)), 4), null_p95=round(float(np.quantile(nulls, 0.95)), 4), zero_clause=(r2 < 0.2))
        j2[ln] = row
    R["J2"] = j2
    del m; gc.collect(); torch.cuda.empty_cache()
    return R

def dump(rep, tag):
    rep["_meta"] = dict(case="E22-black", sha=SHA, sizes=SIZES, elab_s=round(time.time() - T0, 1), stage=tag,
                        _selfcheck="e22_black_ok" if all(r.get("_selftest", {}).get("pass_") for k, r in rep.items() if not k.startswith("_") and isinstance(r, dict)) else "SENTINEL_FAIL")
    json.dump(rep, open("/kaggle/working/report_exp22_black.json", "w"), ensure_ascii=False, indent=1)
    print("REPORT_LINE::" + base64.b64encode(json.dumps(rep, ensure_ascii=False).encode()).decode()[:4000], flush=True)

REP = {}
for sz in SIZES:
    try:
        REP[sz] = run_model(sz); dump(REP, sz)
    except Exception as e:
        REP[sz] = dict(error=repr(e)[:300]); dump(REP, sz + ":ERR")
dump(REP, "final")
print("DONE E22-BLACK", flush=True)
