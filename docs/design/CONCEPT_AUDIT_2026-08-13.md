# shirtfaced — Concept Library Audit

**Date:** 2026-08-13
**Author:** audit against the 2026-08-12 creative direction reset
**Scope:** `TSHIRT_CONCEPT_LIBRARY.md` (260), `BRAND_GARMENT_CONCEPT_LIBRARY.md` (66),
`HEADWEAR_CONCEPT_LIBRARY.md` (70), `RECENT_CREATIVE_RUN_CONCEPT_ARCHIVE_2026-08-10.md` (18).
414 concepts total.

## The test applied

Per the 2026-08-12 reset: **the artwork makes you want the garment; the joke is what
you discover afterwards.** Hard test per concept — would the graphic still look
desirable if you didn't understand the joke? Concepts that pass only because a
caption explains them, or that lean on Australiana props (native wildlife, national
food, suburban infrastructure) as the joke itself, fail this test regardless of how
"technically different" they are from each other.

Three verdicts:
- **KEEP** — passes the test as currently framed.
- **REWORK** — real bones, but the current framing leans on a prop/idiom/repeated
  device that needs to change, or the source document already flagged it as
  conditional.
- **RETIRE** — fails the test outright, or was already retired in the source
  document and that verdict is reaffirmed here.

## Top-line numbers

| Document | KEEP | REWORK | RETIRE | Total |
|---|---|---|---|---|
| TSHIRT_CONCEPT_LIBRARY.md | 203 | 28 | 29 | 260 |
| BRAND_GARMENT_CONCEPT_LIBRARY.md | 65 | 1 | 0 | 66 |
| HEADWEAR_CONCEPT_LIBRARY.md | 69 | 1 | 0 | 70 |
| RECENT_CREATIVE_RUN_ARCHIVE | 13 | 4 | 1 | 18 |
| **Total** | **350** | **34** | **30** | **414** |

(Counts verified against the actual verdict marks below, not estimated —
an earlier draft of this table had the arithmetic wrong.)

Of the 29 RETIRE in the tee library, **25 were already marked RETIRED in the
source** — this audit is reaffirming those, not discovering them fresh. The net
*new* retirements from applying the stricter test are 4 tee concepts (#25, #72,
#74, #151) plus 1 from the archive (C04).

## Read this before touching the KEEP count

**A 350-concept "KEEP" list is not a production queue — it's a filtered library.**
The brand-drift complaint that triggered this audit ("carpark cricket, cooked
sausages, dads, bad parking, karaoke, wheelie bins") was never really about any
single concept failing the desirability test in isolation. Almost all of them
pass it individually — the *Reserve Grade* team photo, the *Consultant* BBQ
portrait, the *Deep End* pool scene are all genuinely strong images on their own.
The drift is a **volume and repetition problem**: too many concepts reach for the
same handful of devices (mobility scooter as punchline, bird-vs-human standoff,
esky/gazebo/BBQ mate-group scene, shopping trolley, wheelie bin) as their engine.
Stacked together in a range, individually-fine concepts read as a themed novelty
pack.

**Device caps applied to the production queue** (this actually is enforced in
the KEEP/REWORK marks below now — corrected from an earlier draft where this
prose didn't match the per-item verdicts):
- **Mobility scooter as punchline:** #47, #79, #135, #162 marked REWORK for this
  reason; #215 NICE RIG kept as the strongest execution (studio automotive
  photography, no rider-as-joke risk).
- **Bird-vs-human or bird-only standoff:** #83, #94, #116, #145, #148, #184,
  #223, #230, #236 marked REWORK; #133 The Great Ballet and #141 Public Enemy
  kept as the strongest, least-generic treatments. Eleven concepts total.
- **Esky/gazebo/BBQ mate-group scenes:** #117, #199, #222, #235 marked REWORK
  for near-duplicate staging. #13, #36, #39, #51 share the same setting but
  were judged individually distinct enough to keep as-is — this cluster wasn't
  thinned as hard as the other three; revisit if the queue still reads BBQ-heavy.
- **Shopping trolley:** #37, #50, #65, #160, #218 — all five marked REWORK.
  No trolley concept currently survives into the queue as marked; that's a
  legitimate outcome, not an oversight.

Everything not listed above is marked REWORK/RETIRE below on its own merits —
these four bullets are the *only* REWORK calls driven by repetition rather than
the concept's own execution. Flagging repetition is the actual point of
"concept curation" the reset asked for — a hard per-concept pass/fail test
doesn't catch a repetition problem; only looking at the shape of the whole
queue does.

## THE MINOR PREMIERS

Named directly by the owner as the reference failure case ("competent graphic,
wrong brand"). Marked **RETIRE** below (#25) — carpark cricket + wheelie-bin icon
is the exact tea-towel-Australiana pattern the hard guardrails already prohibit,
and no amount of execution quality fixes a wrong subject.

## Direct conflict with this session's work

**#78 IBIS AFTER DARK is marked RETIRE in the source** ("ibis + servo is too close
to shorthand Australiana"), and **#109 LOCAL WILDLIFE** is retired for the same
reason ("retire ibis-specific version"). The ibis-on-a-bin illustration composited
onto garments earlier this session (`ibis_bin_chicken__tee-*.png`) is exactly the
subject this document already ruled out, independently and before that image
existed. Flagging this plainly rather than quietly reconciling it — that mockup
exists in the repo and is committed, but per this library's own standing guardrail
it shouldn't go to production as currently framed.

**Resolved 2026-08-13 by the owner: the ibis mockup stays.** This is an explicit,
deliberate exception to #78 and #109's standing retirement, not a reversal of the
underlying rule — future ibis/wildlife-shorthand concepts are still governed by
the guardrail above unless a similar explicit call is made.

---

## TSHIRT_CONCEPT_LIBRARY.md — verdicts

Format: `# NAME — VERDICT — reason` (reason omitted where self-evident from the
KEEP default; given for every REWORK and RETIRE).

### Round 01 (1-30)

1. SHE'LL BE RIGHT — KEEP
2. ONE TRIP — KEEP
3. YEAH NAH — KEEP
4. FUCK IT, WHY NOT — REWORK — wheelie-bin obstacle is suburban-infrastructure shorthand; keep the BMX-stunt-poster energy, swap the obstacle
5. ABSOLUTE WEAPON (object) — KEEP
6. GOOD ON YA — KEEP
7. THE EARLY MARK — KEEP
8. RETIRED — JUST GONNA SEND IT — RETIRE (already retired in source)
9. MATE'S RATES — KEEP
10. NOT MY FIRST RODEO (office chair) — KEEP
11. THE RESERVE GRADE — KEEP
12. NO WORRIES — KEEP
13. BIT OF WEATHER ABOUT — KEEP
14. RETIRED — PROBABLY FINE — RETIRE (already retired in source)
15. FULL CREDIT — KEEP
16. COOKED (chef/sausage) — KEEP
17. THE LAST GOOD IDEA — KEEP
18. RETIRED — STIFF SHIT — RETIRE (already retired in source)
19. WE'LL WORK IT OUT — KEEP
20. CHAMPION (trophy) — KEEP
21. RETIRED — FAIR DINKUM RESEARCH — RETIRE (already retired in source)
22. GET A DOG UP YA — KEEP
23. RETIRED — CLOSE ENOUGH — RETIRE (already retired in source)
24. BIG DAY FOR IT — KEEP
25. **THE MINOR PREMIERS — RETIRE — named reference case; carpark cricket + wheelie-bin icon is tea-towel Australiana regardless of execution quality**
26. HAVE A CRACK — KEEP
27. CAN'T PARK THERE MATE — KEEP
28. LOCAL LEGEND — KEEP
29. STRONG START — KEEP
30. SOMEONE'S DAD — KEEP

### Round 02 (31-70)

31. RETIRED — SHE'S ROOTED — RETIRE (already retired in source)
32. JUST HOLD THIS — KEEP
33. RETIRED — SPECIALIST EQUIPMENT — RETIRE (already retired in source)
34. HE'LL BE RIGHT — KEEP
35. GOOD GEAR — KEEP
36. THE CONSULTANT — KEEP
37. NO PLAN B — REWORK — trolley-hill repetition cluster (see top-line note)
38. BIT WARM — KEEP
39. QUALITY CONTROL — KEEP
40. THE PROFESSIONAL — KEEP
41. RETIRED — GOOD ENOUGH FOR GOVERNMENT WORK — RETIRE (already retired in source)
42. JUST NIPPING OUT — KEEP
43. THE DEEP END — KEEP
44. THAT'LL DO — KEEP
45. MATE, I KNOW A BLOKE — KEEP
46. HALF A JOB — KEEP
47. FULL SEND / LOW SPEED — REWORK — mobility-scooter repetition cluster (see top-line note)
48. THE BACKUP PLAN — KEEP
49. NOT IDEAL — KEEP
50. CLOSE CALL — REWORK — trolley repetition cluster
51. ABSOLUTE SCENES — KEEP
52. THE CHOSEN ONE (bottle opener) — KEEP
53. RETIRED — SERVICE HISTORY — RETIRE (already retired in source)
54. SENIOR MANAGEMENT — KEEP
55. RETIRED — FIVE MINUTE JOB — RETIRE (already retired in source)
56. RETIRED — JUST EYEBALL IT — RETIRE (already retired in source)
57. TOO EASY (stubby holder) — KEEP
58. THE STRATEGY MEETING — KEEP
59. RETIRED — PLENTY OF LIFE LEFT — RETIRE (already retired in source)
60. THAT'S NOT GOING ANYWHERE (trailer) — KEEP
61. EARLY KNOCK — KEEP
62. I KNOW WHAT I'M DOING — KEEP
63. THE GOOD SCISSORS — KEEP
64. DON'T WORRY ABOUT IT — KEEP
65. RUN IT BACK — REWORK — trolley repetition cluster
66. CLUB LEGEND — KEEP
67. ALL UNDER CONTROL — KEEP
68. PRETTY SURE — KEEP
69. ONE OF THE GREATS — KEEP
70. THE APPRENTICE — KEEP

### Round 03 (71-120)

71. YEAH RIGHTO — KEEP
72. THE MAGPIE — RETIRE — native-wildlife shorthand; source's own "retain only if it transcends Australiana" condition isn't met by the description as written
73. BUSINESS CLASS — KEEP
74. FROTH & FURY — RETIRE — same wildlife-shorthand risk as #72
75. MAY CONTAIN TRACES OF POOR JUDGEMENT — KEEP
76. THE AUSTRALIAN DREAM — RETIRE (already retired in source)
77. NICE ONE DICKHEAD — KEEP
78. IBIS AFTER DARK — RETIRE (already retired in source) — see "direct conflict" section above
79. GIVE IT A NUDGE — REWORK — mobility-scooter repetition cluster
80. AUSTRALIAN FORMALWEAR — RETIRE (already retired in source)
81. NO DRAMAS — KEEP
82. MUM SAID NO — KEEP
83. THE ESCORT — REWORK — bird repetition cluster
84. JUST ONE — KEEP
85. HEROES GET REMEMBERED — KEEP
86. THE GETAWAY — KEEP
87. NOT TODAY, CHAMP — KEEP
88. BIN NIGHT — RETIRE (already retired in source)
89. THE PEACOCK — KEEP — not Australian-specific, strong image; see also archive B04 which retains it
90. I'VE HAD WORSE IDEAS — KEEP
91. SOCIAL ATHLETE — KEEP
92. BUSH CHOOK — RETIRE (already retired in source)
93. UNSUPERVISED — KEEP
94. THE STANDOFF — REWORK — bird repetition cluster
95. FANCY AS FUCK — KEEP
96. NOTHING TO SEE HERE — KEEP
97. DEADSET — KEEP
98. THE KING (streetlight) — REWORK — source itself conditions this on dropping the bird-on-streetlight framing
99. OUTSTANDING CITIZEN — KEEP
100. SHIT HOT — KEEP
101. WRONG WAY, GO BACK — RETIRE (already retired in source)
102. THE DROP BEAR — RETIRE (already retired in source)
103. CERTIFIED UNIT — REWORK — livestock/agricultural-show framing risks reading rural-Australiana; keep only if genuinely elevated past that
104. GET FUCKED — KEEP
105. THE LAST SAUSAGE — KEEP — source explicitly notes it's not dependent on national-food shorthand
106. FINE DINING — KEEP
107. GOOD SORT — KEEP
108. I'M NOT HERE TO FUCK SPIDERS — KEEP
109. LOCAL WILDLIFE — RETIRE (already retired in source) — see "direct conflict" section above
110. FUCK YEAH — KEEP
111. THE INVITATION — KEEP
112. BIT OF CULTURE — KEEP
113. FUCK AROUND / FIND OUT — KEEP
114. PREMIUM MEMBER — KEEP
115. YOU BEAUTY — KEEP
116. THE WITNESS — REWORK — bird/animal repetition cluster; source already conditions species choice
117. WE'RE GONNA NEED A BIGGER ESKY — REWORK — esky/BBQ repetition cluster, source conditions the phrasing
118. FUCK KNOWS — KEEP
119. PEAK CONDITION — KEEP
120. shirtfaced (brand hero) — KEEP

### Round 04 (121-180)

121. THE BOUNCER — RETIRE (already retired in source)
122. ABSOLUTELY FUCKED — KEEP
123. THE INCIDENT — KEEP
124. WORLD CHAMPION (dog boxing) — KEEP
125. BIT FUCKEN WARM — KEEP
126. NO IDEA — KEEP
127. THE ESCAPE — KEEP
128. COOKED (ice cream) — KEEP
129. NICE PARK, DICKHEAD — KEEP
130. shirtfaced social club — KEEP
131. WORLD TOUR — KEEP
132. TOO EASY (wordmark) — KEEP
133. THE GREAT BALLET — KEEP — bird repetition cluster, but this is the pick to keep from that cluster (see top-line note)
134. NATIONAL TREASURE — RETIRE (already retired in source)
135. GET IN, LOSER — REWORK — mobility-scooter repetition cluster
136. SHE'LL BE RIGHT (sliding type) — KEEP
137. THE LAST CHIP — KEEP
138. BREAKFAST — RETIRE (already retired in source)
139. FUCKIN' OATH — KEEP
140. THE PROPHECY — KEEP
141. PUBLIC ENEMY — KEEP — bird repetition cluster, second pick to keep (see top-line note)
142. I KNOW A SHORTCUT — KEEP
143. NAN'S GOT THIS — KEEP
144. VERY IMPORTANT PERSON — KEEP
145. THE MEETING (birds) — REWORK — bird repetition cluster
146. PRETTY FUCKEN GOOD — KEEP
147. ZERO FUCKS RACING — KEEP
148. THE KING'S SPEECH — REWORK — bird repetition cluster
149. AFTERNOON DELIGHT — KEEP
150. FUCK ME DEAD — KEEP
151. BUSH TELEGRAPH — RETIRE — source conditions on not leaning on idiom+wildlife; the idiom itself is the risk
152. OFFICIAL BUSINESS — KEEP
153. MATE — KEEP
154. THE LOCAL — RETIRE (already retired in source)
155. YEAH NAH UNIVERSITY — KEEP
156. DREAM BIG — KEEP
157. THAT'S NOT GOING ANYWHERE (straps) — KEEP
158. shirtfaced hardware — REWORK — source conditions on avoiding fake-Australian-hardware nostalgia
159. OLD MATE — KEEP
160. THE CHOSEN ONE (trolleys) — REWORK — trolley repetition cluster
161. PISSFIT — KEEP
162. NOT MY FIRST RODEO (scooter) — REWORK — mobility-scooter repetition cluster
163. SPACE PROGRAM — REWORK — source conditions on dropping "Australian Space Program" wording
164. CHAMPION (object on plinth) — KEEP
165. DO SOMETHING STRANGE FOR A CHANGE — KEEP
166. THE ADVISER — KEEP
167. GOOD LUCK WITH THAT — KEEP
168. THE SECOND WIND — KEEP
169. NATURE IS HEALING — KEEP
170. shirtfaced country club — KEEP
171. YOU CAN'T PARK THERE MATE — KEEP
172. THE BACHELOR — KEEP
173. MILDLY CONCERNING — KEEP
174. FUCKING MAJESTIC — KEEP
175. THREE FOR THE ROAD — RETIRE (already retired in source)
176. EXPERT — KEEP
177. THE FINAL BOSS — KEEP
178. DAD BOD ATHLETIC CLUB — KEEP
179. ONE OF THOSE NIGHTS — KEEP
180. shirtfaced (flagship) — KEEP

### Round 05 — garment-led (181-220)

181. THE DIVORCEE — KEEP
182. FUCK AROUND / FIND OUT (hoodie) — KEEP
183. HOT GIRL ADMIN — KEEP
184. THE NEGOTIATOR — REWORK — bird repetition cluster
185. FUCK OFF, I'M BUSY — KEEP
186. SUNDAY SERVICE — REWORK — servo setting risks Australian-shorthand; source already flags this
187. SPORTS BRA ENERGY — KEEP
188. THE PROBLEM SOLVER — KEEP
189. LOCAL HOT SINGLE — KEEP
190. SNAKE EYES — KEEP
191. FUCK YEAH UNIVERSITY — KEEP
192. THE SUPERVISOR — KEEP
193. GOOD TITS, GREAT PERSONALITY — KEEP
194. THE PUB TEST — KEEP
195. RUNNING LATE — KEEP
196. NIGHT SHIFT — KEEP
197. MUM'S GOOD TOWELS — KEEP
198. FUCKING DELIGHTFUL — KEEP
199. WEATHER EVENT — REWORK — esky/gazebo repetition cluster
200. NOBODY PANIC — KEEP
201. THE RECOVERY POSITION — KEEP
202. CROP DUSTER — KEEP
203. THE GOOD ROOM — KEEP
204. YEAH THE GIRLS — KEEP
205. FRESH AS A DAISY — KEEP
206. THE SECURITY DETAIL — KEEP
207. FANCY SEEING YOU HERE — KEEP
208. DOING FUCK ALL — KEEP
209. NO BRAINS, ALL HEART — KEEP
210. THE COMMITTEE — KEEP
211. WELL BEHAVED WOMEN — KEEP
212. SHUT THE GATE — KEEP
213. PARKING INSPECTOR — KEEP
214. THE LAST RESORT — KEEP
215. NICE RIG — KEEP — the pick to keep from the mobility-scooter cluster (see top-line note)
216. PULL YOUR HEAD IN — KEEP
217. ABSOLUTE PRINCESS — KEEP
218. CAN'T TAKE YOU ANYWHERE — REWORK — trolley repetition cluster
219. HOME BY NINE — KEEP
220. HAVE YOU TRIED TURNING IT OFF AND ON? — KEEP

### Round 06 — no adult supervision (221-260)

221. THE GIRLS ARE FINE — KEEP
222. THE BOYS ARE FINE — REWORK — esky/BBQ repetition cluster
223. FRONT TOWARD ENEMY — REWORK — bird repetition cluster
224. MATE, MOVE — KEEP
225. THE WEDDING SINGER — KEEP
226. FUCKING FREEZING — KEEP
227. THE REBOUND — KEEP
228. CATCH OF THE DAY — KEEP
229. DON'T START — KEEP
230. THE NEIGHBOURHOOD WATCH — REWORK — bird/animal repetition cluster
231. MAIN CHARACTER — KEEP
232. OLD GIRL — KEEP
233. FUCKING FABULOUS — KEEP
234. THE VISITOR — KEEP
235. SOME ASSEMBLY REQUIRED — REWORK — esky/gazebo repetition cluster
236. GOOD CHAT — REWORK — bird repetition cluster
237. DON'T BE A DICKHEAD — KEEP
238. SHE GOES ALRIGHT — KEEP
239. MORNING PERSON — KEEP
240. SOCIAL BATTERY — KEEP
241. GET YOUR OWN — KEEP
242. HARD LAUNCH — KEEP
243. I'M WITH STUPID — KEEP
244. FUCKING OUTSTANDING — KEEP
245. THE KIDS TABLE — KEEP — see also archive B01, which recalibrates the same concept
246. BAD INFLUENCE — KEEP
247. GOOD INFLUENCE — KEEP
248. FUCK THIS SHIT — KEEP
249. THE DESIGNATED DRIVER — KEEP
250. UNFUCKWITHABLE — KEEP
251. THE FUNCTIONING ADULT — KEEP
252. FUCK AROUND & FLOURISH — KEEP
253. THE LONG WEEKEND — KEEP
254. CHUCK A SICKIE — KEEP
255. GET YOUR SHIT TOGETHER — KEEP
256. NOT HERE TO FUCK SPIDERS (spider back print) — KEEP
257. FUCK ME, IT'S MONDAY — KEEP
258. THE COMEBACK — KEEP
259. GOOD MATES — KEEP
260. shirtfaced (democratic core) — KEEP

---

## BRAND_GARMENT_CONCEPT_LIBRARY.md — verdicts

This whole document is brand-mark/crest/typography execution, not gag-illustration —
it's already the safest lane in the library relative to the reset, since there's no
prop to over-lean on. **KEEP B01–B58, B60–B66 (65 of 66).**

- B59 **Surf Club** — REWORK — source already conditions this on reading contemporary streetwear rather than souvenir/surf nostalgia; the risk is real enough to flag.

## HEADWEAR_CONCEPT_LIBRARY.md — verdicts

Same read as the brand library — disciplined, small-scale, typography/embroidery-led.
**KEEP H01–H61, H63–H70 (69 of 70).**

- H62 **The Straw** — REWORK — source already conditions this on reading fashion/sport rather than Australiana.

## RECENT_CREATIVE_RUN_CONCEPT_ARCHIVE_2026-08-10.md — verdicts

This document already runs a near-identical test (the "COSTUME TEST": does the
concept survive when you strip the borrowed visual costume). Mapping its existing
status language onto this audit's verdicts rather than re-deriving:

- A01 YOU'RE NOT WELCOME — KEEP (was STRONG/DEVELOP)
- A02 COME AS YOU ARE. DON'T BE A DICKHEAD. — KEEP (was STRONG/DEVELOP)
- A03 ABSOLUTE WEAPON — ordinary-person lane — KEEP (was STRONG/DEVELOP)
- A04 HOLD MY BEER — REWORK (was RETAIN/RECALIBRATE)
- A05 RARE WIN — REWORK (was RETAIN/RECALIBRATE)
- A06 EVERYONE WELCOME. NO DICKHEADS. — KEEP (was STRONG/DEVELOP)
- B01 THE KIDS TABLE — KEEP (was RETAIN/RECALIBRATE — the main library's #245 already reflects the recalibration, promoting to KEEP here)
- B02 MUM SAID NO — KEEP (was RETAIN/RECALIBRATE — same reasoning, #82 in main library already stands as KEEP)
- B03 NICE ONE DICKHEAD — KEEP (was STRONG/DEVELOP)
- B04 THE PEACOCK — KEEP (was RETAIN/RECALIBRATE — main library #89 already stands as KEEP)
- B05 FANCY AS FUCK — KEEP (was STRONG/DEVELOP)
- B06 THE CONSULTANT — KEEP (was STRONG/DEVELOP)
- C01 I MEANT TO DO THAT — REWORK (was RETAIN/RECALIBRATE)
- C02 shirtfaced COUNTRY CLUB — KEEP (was STRONG/DEVELOP) — genuinely the clearest example of the new principle already working: "should genuinely pass as expensive clubwear before the stupidity arrives"
- C03 BEAUTIFUL FORM — REWORK (was RETAIN/RECALIBRATE)
- C04 NOT FUCKING LEAVING — RETIRE (was REJECT EXECUTION/KEEP LEARNING) — the document's own conclusion: "typography cannot rescue the absence of human truth"
- C05 THE AFTERPARTY — KEEP (was STRONG/DEVELOP)
- C06 WORLD CHAMPION (boot) — KEEP (was STRONG CONCEPT/RETREATMENT REQUIRED — treatment note already resolved: drop the borrowed Japanese-boxing-poster identity, keep the sporting disproportion)

---

## What this doesn't do

This audit judges each concept against the hard test and flags the four repetition
clusters. It does **not** rebuild the production queue — that's a separate,
smaller editorial pass: pick the 1-2 survivors from each repetition cluster,
combine with the clean KEEPs, and sequence. That's a curation call, not an audit
call, and belongs to whoever's building the actual queue next.
