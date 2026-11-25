#!/bin/bash
# Farm runner fix-round test (Nov 24-25). Runs in a scratch HOME (/tmp/fx), never your real run folders.
# fixcheck.sh — reruns every failing audit case (#1-#6, #13, #21, #24-#29, #32)
# and the VERIFICATION regression cases (a)-(n) against the fixed runner.
export HOME=/tmp/fx; rm -rf $HOME; mkdir -p $HOME
# Live status goes to a scratch file during tests, never into the repo.
export FARM_STATUS_OUT=/tmp/fx/farm-status.json
export FARM_NO_PUBLISH=1
# Glam, Nov 25: tests run in test mode with their own throwaway Mila key;
# the real key lives only in Mila's own session.
export FARM_TEST_MODE=1
python3 -c "import os;open('/tmp/fx_mila_key','w').write(os.urandom(32).hex())"
export MILA_SIGNING_KEY=/tmp/fx_mila_key
export FARM_TEST_MILA_PUBKEY=$(python3 -c "import sys;sys.path.insert(0,'$(cd "$(dirname "$0")" && pwd)');import ed25519 as e;print(e.public_key(bytes.fromhex(open('/tmp/fx_mila_key').read().strip())).hex())")
R="python3 $(cd "$(dirname "$0")" && pwd)/runner.py"
P=0; F=0
ok(){ P=$((P+1)); echo "PASS  $1 :: $2"; }
bad(){ F=$((F+1)); echo "FAIL  $1 :: $2"; }
# expect <label> <grep-pattern> <text>
expect(){ if echo "$3" | grep -qE -- "$2"; then ok "$1" "$(echo "$3" | grep -E -- "$2" | head -1 | sed 's/  */ /g' | cut -c1-150)"; else bad "$1" "$(echo "$3" | head -3 | tr '\n' ' ' | cut -c1-200)"; fi; }
python3 -c "open('/tmp/fx_p.png','wb').write(b'\x89PNG\r\n\x1a\n')"
# Glam, Nov 25: runs refuse an old rules copy (tests compare against the repo
# copy), builds are measured (real tiny mp4s), Mila's gates need her signature.
ROOTF="$(cd "$(dirname "$0")/.." && pwd)"
export FARM_LIVE_RULES_URL="file://$ROOTF/farm-rules.json"
ffmpeg -v error -y -f lavfi -i color=c=black:s=16x16:r=1 -t 34 -c:v libx264 -pix_fmt yuv420p /tmp/fx_base34.mp4
ffmpeg -v error -y -f lavfi -i color=c=black:s=16x16:r=1 -t 8 -c:v libx264 -pix_fmt yuv420p /tmp/fx_base8.mp4
ffmpeg -v error -y -f lavfi -i color=c=black:s=16x16:r=1 -t 5 -c:v libx264 -pix_fmt yuv420p /tmp/fx_base5.mp4
# vid <path> <tag> [base]: a real 34 s mp4 made unique by a trailing 'free' box
vid(){ python3 -c "import sys,struct;b=open(sys.argv[3],'rb').read();t=sys.argv[2].encode();open(sys.argv[1],'wb').write(b+struct.pack('>I4s',8+len(t),b'free')+t)" "$1" "$2" "${3:-/tmp/fx_base34.mp4}"; }
# sv <out> <run> <verdict> <builds-dir>: Mila signs a Step 10 verdict on the exact builds
sv(){ local a=(); for f in "$4"/*.mp4; do a+=(--file "$f"); done; $R mila-sign --run "$2" --step 10 --verdict "$3" "${a[@]}" --out "$1" >/dev/null; }

# ---------- #13 create with no pick/model
OUT=$($R create --mode "Get Ready With Me" 2>&1); expect "#13 create without --pick/--model" "^Created" "$OUT"
RUN=run-$(date +%F)-1; D=$HOME/workspace/farm-runs/$RUN/steps
OUT=$($R status $RUN 2>&1); expect "#13 status header with empty pick/model" "pick at Step 3" "$OUT"
echo "Findings: x" > $D/step2-scout/scout.md
# ---------- #6 story person words
for s in "Every guy needs a jacket that survives game night." "For the dad who stands at the grill all summer." "For anyone whose feet ache after a double shift."; do
  printf 'Findings: x\nStory: %s\n' "$s" > $D/step2-scout/scout.md
  OUT=$($R status $RUN); expect "#6 story passes: $s" "Step 2 +Scout +CLEARED" "$OUT"; done
printf 'Findings: x\nStory: Her silk press deserves a pillow that keeps it fresh.\n' > $D/step2-scout/scout.md
OUT=$($R status $RUN); expect "#25 'silk press' not a fabric spec (story)" "Step 2 +Scout +CLEARED" "$OUT"
printf 'Findings: x\nStory: Plant based massage oil made with turmeric and honey.\n' > $D/step2-scout/scout.md
OUT=$($R status $RUN); expect "(i) label story still fails" "Step 2 +Scout +WAITING.*spec" "$OUT"
printf 'Findings: x\nStory: My skin has been dry and tight all winter, and I just want to feel soft again.\n' > $D/step2-scout/scout.md
OUT=$($R status $RUN); expect "(i) real first-person story still clears" "Step 2 +Scout +CLEARED" "$OUT"
rm $D/step2-scout/scout.md; OUT=$($R status $RUN); expect "(h) no scout file waits" "Step 2 +Scout +WAITING" "$OUT"
printf 'Findings: x\n' > $D/step2-scout/scout.md; OUT=$($R status $RUN); expect "(h) findings only, no Story line waits" "no 'Story:' line" "$OUT"
printf 'Findings: x\nStory: Your feet hurt all week and you deserve a soft landing.\n' > $D/step2-scout/scout.md
# ---------- #13 pick from pick.md
OUT=$($R status $RUN); expect "#13 Step 3 waits without pick.md" "Step 3 +Pick +WAITING" "$OUT"
printf 'product: TEST Cloud Slides\nlisting: test\n' > $D/step3-pick/pick.md
OUT=$($R status $RUN); expect "#13 Step 3 clears from pick.md" "Step 3 +Pick +CLEARED +pick recorded: TEST Cloud Slides" "$OUT"
# ---------- (a)-(c) photo + match gates
OUT=$($R status $RUN); expect "(a) no photo -> blocked at Step 4" "HEADLINE: BLOCKED at Step 4" "$OUT"
OUT=$($R check $RUN --to 6; echo "exit $?"); expect "(b) check --to 6 refuses without match" "exit 2" "$OUT"
$R attach-photo $RUN /tmp/fx_p.png --by Indigo >/dev/null
$R record-match $RUN --checker Indigo --grabber Indigo --verdict MATCH >/dev/null
OUT=$($R status $RUN); expect "(c) self-signed match refused" "Step 5 .*INVALID.*signed by the grabber" "$OUT"
$R record-match $RUN --checker Mila --grabber Indigo --verdict MATCH >/dev/null
OUT=$($R status $RUN); expect "(c) independent match clears" "Step 5 .*CLEARED" "$OUT"
# ---------- script checks
S=$D/step6-script/script.md
sc(){ printf "%b" "$2" > $S; OUT=$($R status $RUN | grep 'Step 6 '); expect "$1" "$3" "$OUT"; }
sc "#5 second CTA 'grab yours from the link below' fails" 'CTA: linked below\nLINE 1: "Your feet hurt after every shift."\nLINE 2: "Grab yours from the link below."\nLINE 3: "Tap the orange cart."\n' "INVALID.*cta-position"
sc "#5 'Shop now' mid-script fails" 'CTA: linked below\nLINE 1: "Your feet hurt after every shift."\nLINE 2: "Shop now before they are gone."\nLINE 3: "Tap the orange basket."\n' "INVALID.*cta-position"
sc "#5 'click the link' banned" 'CTA: linked below\nLINE 1: "Your feet hurt after every shift."\nLINE 2: "Click the link below."\n' "INVALID.*tap-the-link"
sc "#5 'link in my bio' mid-script fails" 'CTA: linked below\nLINE 1: "Your feet hurt after every shift."\nLINE 2: "Link in my bio, sis."\nLINE 3: "They feel like clouds."\n' "INVALID.*cta-position"
sc "#5 'tap the link' still banned" 'CTA: linked below\nLINE 1: "Your feet hurt after every shift."\nLINE 2: "Tap the link."\n' "INVALID.*tap-the-link"
sc "#5 cart CTA mid-script fails" 'CTA: linked below\nLINE 1: "Your feet hurt after every shift."\nLINE 2: "Tap the orange cart."\nLINE 3: "They feel like clouds."\n' "INVALID.*cta-position"
sc "CLAIMS 'hair growth' spoken fails" 'CTA: linked below\nLINE 1: "Your edges need love after every long shift."\nLINE 2: "This hair growth oil sits by the sink."\n' "INVALID.*health-claim"
sc "CLAIMS 'clears acne' spoken fails" 'CTA: linked below\nLINE 1: "Your skin feels tight by noon every day."\nLINE 2: "This one clears acne overnight."\n' "INVALID.*health-claim"
sc "CLAIMS 'anti-aging' spoken fails" 'CTA: linked below\nLINE 1: "Your skin feels tight by noon every day."\nLINE 2: "Anti-aging cream right by the sink."\n' "INVALID.*health-claim"
sc "CLAIMS 'heals' spoken fails" 'CTA: linked below\nLINE 1: "Your feet hurt after every long shift."\nLINE 2: "This balm heals cracked heels."\n' "INVALID.*health-claim"
sc "CLAIMS 'FDA approved' spoken fails" 'CTA: linked below\nLINE 1: "Your skin feels tight by noon every day."\nLINE 2: "It is FDA approved."\n' "INVALID.*health-claim"
sc "CLAIMS 'weight loss' spoken fails" 'CTA: linked below\nLINE 1: "Your mornings are rushed every single day."\nLINE 2: "A weight loss tea for busy mornings."\n' "INVALID.*health-claim"
sc "CLAIMS 'regrow' spoken fails" 'CTA: linked below\nLINE 1: "Your edges need love after every long shift."\nLINE 2: "Made to regrow thin edges."\n' "INVALID.*health-claim"
sc "CLAIMS 'treats eczema' spoken fails" 'CTA: linked below\nLINE 1: "Your skin feels tight by noon every day."\nLINE 2: "It treats eczema patches."\n' "INVALID.*health-claim"
sc "CLAIMS claim in CTA line fails" 'CTA: the hair growth oil is linked below\nLINE 1: "Your edges need love after every long shift."\n' "INVALID.*health-claim"
sc "CLAIMS claim in Caption line fails" 'CTA: linked below\nCaption first line: Scalp oil that cures dandruff, linked below\nLINE 1: "Your edges need love after every long shift."\n' "INVALID.*health-claim"
sc "CLAIMS 'treat yourself' passes" 'CTA: linked below\nLINE 1: "You worked all day, so treat yourself tonight."\n' "WAITING.*passing"
sc "CLAIMS 'a little treat' passes" 'CTA: linked below\nLINE 1: "You deserve a little treat after every shift."\n' "WAITING.*passing"
sc "#5 one closing CTA passes" 'CTA: it is linked below for you\nLINE 1: "Your feet hurt after every long shift."\nLINE 2: "These slip on and feel like clouds."\nLINE 3: "Tap the orange cart."\n' "WAITING.*passing the script check"
sc "#25 'I used to' not a use claim" 'CTA: linked below\nLINE 1: "You know I used to dread mornings, right?"\n' "WAITING.*passing"
sc "#25 'priceless' not a price" 'CTA: linked below\nLINE 1: "Your face when she says the look is priceless."\n' "WAITING.*passing"
sc "#25 'sold out' relabeled urgency" 'CTA: linked below\nLINE 1: "You will be sad when they are sold out."\n' "INVALID.*urgency"
sc "#25 real price still fails" 'CTA: linked below\nLINE 1: "You get this whole price for nothing."\n' "INVALID.*price"
sc "#26 model-voice hook fails" 'CTA: linked below\nLINE 1: "I am obsessed with how soft my skin feels."\n' "INVALID.*hook"
sc "#26 viewer hook passes" 'CTA: linked below\nLINE 1: "Your skin feels tight by noon every day."\n' "WAITING.*passing"
sc "#27 Hook: row is read and checked" 'CTA: linked below\nHook: "Specs polyester true to size for you."\nLINE 1: "Your feet hurt after every shift."\n' "INVALID.*spec"
sc "#27 lowercase line row read" 'CTA: linked below\nline 1: "You know that feeling when your feet really hurt after a long shift."\n' "INVALID.*line-length"
sc "#21 mode name 'Quick Tip' as opener fails" 'CTA: linked below\nLINE 1: "Quick tip for you girls."\n' "INVALID.*mode-name-hook"
sc "#21 mode name 'Outfit'-style unlisted opener ok" 'CTA: linked below\nLINE 1: "Outfit check for you girls."\n' "WAITING.*passing"
sc "#21 'What I Actually Use' opener fails" 'CTA: linked below\nLINE 1: "What I actually use when you ask me."\n' "INVALID"
sc "(j) 13 words fails" 'CTA: linked below\nLINE 1: "You know that feeling when your feet really hurt after a long shift."\n' "INVALID.*line-length"
sc "(j) no CTA line fails" 'LINE 1: "Your feet hurt after every shift."\n' "INVALID.*no-cta"
sc "(k) GRWM opener fails" 'CTA: linked below\nLINE 1: "Get ready with me, you deserve this."\n' "INVALID.*mode-name-hook"
sc "(k) 'has been living on my counter' fails" 'CTA: linked below\nLINE 1: "You see this? It has been living on my counter."\n' "INVALID.*use-claim"
sc "(l) dress spec percent fails" 'CTA: linked below\nLINE 1: "You will love this, ninety percent soft."\n' "INVALID.*spec"
sc "(l) viewer 'all week' passes" 'CTA: linked below\nLINE 1: "Your feet hurt all week, right?"\n' "WAITING.*passing"
sc "(l) 'my go-to' fails" 'CTA: linked below\nLINE 1: "You need my go-to for winter."\n' "INVALID.*use-claim"
# ---------- #24 drive msg on failing script
printf 'CTA: linked below\nLINE 1: "I am obsessed with how soft my skin feels."\n' > $S
OUT=$($R drive $RUN); expect "#24 drive on failing script names the failure" "FAILS the script check and goes back to the Story Agent" "$OUT"
OUT=$($R approve-script $RUN --by Mila; echo "exit $?"); expect "(j) approve refused on failing script" "APPROVAL REFUSED" "$OUT"
# ---------- #3 approval tied to script
printf 'CTA: it is linked below for you\nLINE 1: "Your feet hurt after every long shift."\nLINE 2: "Tap the orange cart."\n' > $S
OUT=$($R drive $RUN); expect "(g) drive stops at Mila's script approval, not Glam's" "waiting on Mila's script approval" "$OUT"
$R approve-script $RUN --by Mila >/dev/null
OUT=$($R status $RUN); expect "#3 approved script clears" "Step 6 +Script +CLEARED" "$OUT"
printf 'CTA: linked below\nLINE 1: "Your mornings are chaos and you need a win."\nLINE 2: "Tap the orange cart."\n' > $S
OUT=$($R status $RUN); expect "#3 edited script loses approval" "Step 6 +Script +WAITING +script changed after Mila's approval" "$OUT"
OUT=$($R drive $RUN); expect "#3 drive asks Mila again" "changed after Mila's approval" "$OUT"
$R approve-script $RUN --by Mila >/dev/null
# ---------- Step 7/8 lint
cp /tmp/fx_p.png $D/step7-styled/model.png
$R approve-image $RUN --by Mila >/dev/null  # chain: Mila approves the model photo (Step 7 gate)
K=$D/step8-package/package.md
CAP='Caption: Cloud Slides linked below for your tired feet\n#cloudslides #slides #comfyslides\n'
lint(){ printf "%b" "$2$CAP" > $K; OUT=$($R lint $RUN 2>&1); expect "$1" "$3" "$OUT"; }
lint "#4 jar/tube/'product in her hand' fails" 'References: approved styled image + the real listing photo\nClip 2: she picks up the jar and lifts it to camera.\nClip 3: she holds the tube up next to her face.\nClip 4: product in her hand, spraying.\n' "LINT RESULT: FAIL"
OUT2=$(echo "$OUT" | grep -c "\[DRAWN PRODUCT\]"); [ "$OUT2" -ge 3 ] && ok "#4 three handling lines caught" "DRAWN PRODUCT findings: $OUT2" || bad "#4 three handling lines caught" "DRAWN PRODUCT findings: $OUT2"
lint "EVERY a jar drawn on the counter now fails (real listing photo only)" 'References: approved styled image + the real listing photo\nC01 - 8 seconds. She smiles at the counter, the jar sits on the counter untouched.\n' "LINT RESULT: FAIL"
lint "#28 five 10-second clips fail" 'References: styled image + listing photo\nClip 1 (10 seconds): "one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen"\nClip 2 (10 seconds)\nClip 3 (10 seconds)\nClip 4 (10 seconds)\nClip 5 (10 seconds)\n' "LINT RESULT: FAIL"
echo "$OUT" | grep -q "max 12 spoken words" && ok "#28 >12 words in a clip caught" "$(echo "$OUT"|grep -m1 'max 12')" || bad "#28 >12 words" "$OUT"
echo "$OUT" | grep -q "8 seconds flat" && ok "#28 10-second clip caught" "$(echo "$OUT"|grep -m1 '8 seconds flat'|cut -c1-120)" || bad "#28 10-second clip" ""
echo "$OUT" | grep -q "5 clips declared" && ok "#28 five clips caught" "$(echo "$OUT"|grep -m1 'clips declared'|cut -c1-120)" || bad "#28 five clips" ""
lint "#28 four 8s clips + 2s close-up pass" 'References: approved styled image + the real listing photo\nC01 - 8 seconds, she smiles at the counter.\nC02 - 8 seconds.\nC03 - 8 seconds.\nC04 - 8 seconds.\nC05 - close-up, 2 seconds of the real listing photo.\n' "package passes"
lint "(d) Nov 24 failure recipe fails" 'References: styled image\nnever spoken, never mouthed\nBOTTLE: the exact product: a tall rectangular clear bottle, the label reads Amococo, TURMERIC, 200ml\nShe tips the bottle over her open palm and golden oil pools in it; she holds the bottle.\n' "LINT RESULT: FAIL"
for c in "RETIRED GUARD TEXT" "LABEL WORDING" "PRODUCT DESCRIPTION" "DRAWN PRODUCT" "REFERENCES"; do echo "$OUT" | grep -q "\[$c\]" && ok "(d) catches $c" "$(echo "$OUT"|grep -m1 "\[$c\]"|cut -c1-110)" || bad "(d) catches $c" ""; done
touch $D/step8-package/staging-proof.md
lint "(n-a) pour + proof still fails" 'References: approved styled image + the real listing photo\nShe pours the oil.\n' "LINT RESULT: FAIL"
lint "EVERY texture shot with the bottle in frame now fails" 'References: approved styled image + the real listing photo\nTexture shot: the serum on her skin, the bottle stays on the counter.\n' "LINT RESULT: FAIL"
lint "EVERY use shot, product off frame, passes" 'References: approved styled image + the real listing photo\nUse shot: she works the oil into her scalp with her fingertips, product off frame.\n' "package passes"
lint "EVERY two use shots pass (no one-shot limit)" 'References: approved styled image + the real listing photo\nUse shot: she smooths the cream over her hands.\nUse shot: she pats her cheeks.\n' "package passes"
lint "(n-f) dress fabric moving + proof passes" 'References: approved styled image + the real listing photo\nShow-it shot: fabric moving as she turns.\n' "package passes"
lint "(n-g) shoes walking + proof passes" 'References: approved styled image + the real listing photo\nShow-it shot: shoes on feet walking down the sidewalk.\n' "package passes"
lint "EVERY a gadget drawn in use fails" 'References: approved styled image + the real listing photo\nShow-it shot: the mister in use, spraying a fine mist.\n' "LINT RESULT: FAIL"
rm $D/step8-package/staging-proof.md
lint "EVERY 'the gadget in use' is a drawn product, fails" 'References: approved styled image + the real listing photo\nShow-it shot: the gadget in use.\n' "LINT RESULT: FAIL"
printf "%b" 'References: approved styled image + the real listing photo\nC01 - 8 seconds, she smiles at the counter, product stationary.\n'"$CAP" > $K
OUT=$($R check $RUN --to 9; echo "exit $?"); expect "(d) clean package clears to 9" "CHECK to Step 9: OK" "$OUT"
# ---------- builds, handoff, verdicts (#1, #2, (f))
vid $D/step9-builds/v1.mp4 fake1
OUT=$($R drive $RUN); expect "(f) auto-handoff then stop at Mila" "STOP at Step 10 — human gate: Mila" "$OUT"
H=$HOME/workspace/farm-qc-handoff/$RUN
OUT=$($R review-decision $RUN --decision approved; echo "exit $?"); expect "(f) review decision refused before PASS" "REVIEW DECISION REFUSED" "$OUT"
sv $H/verdict.md $RUN FAIL $D/step9-builds
OUT=$($R drive $RUN); N=$(echo "$OUT" | grep -c "Collected Mila's verdict")
[ "$N" = 1 ] && ok "#2 FAIL collected exactly once" "Collected lines: $N" || bad "#2 FAIL collected once" "Collected lines: $N"
N=$(grep -c "Auto-collected" $HOME/workspace/farm-runs/$RUN/RUN-SHEET.md); [ "$N" = 1 ] && ok "#2 run sheet logs one collection" "Auto-collected lines: $N" || bad "#2 run sheet logs" "$N"
ls $H | grep -q "^verdict-collected-" && [ ! -e $H/verdict.md ] && ok "#1 verdict.md moved after collection" "$(ls $H | grep verdict)" || bad "#1 verdict moved" "$(ls $H)"
OUT=$($R drive $RUN); N=$(echo "$OUT" | grep -c "Collected"); [ "$N" = 0 ] && ok "#2 second drive re-collects nothing" "$(echo "$OUT"|tail -1|cut -c1-120)" || bad "#2 second drive" "$N"
OUT=$($R status $RUN); expect "#1 FAIL stops the run" "Step 10 .*INVALID.*FAIL" "$OUT"
vid $D/step9-builds/v2.mp4 fake2
OUT=$($R status $RUN); expect "#1 new build after FAIL waits for Mila (old FAIL not reused)" "Step 10 .*WAITING +new build since Mila's verdict" "$OUT"
OUT=$($R drive $RUN); expect "#1 driver hands off the new build" "Auto-handoff" "$OUT"
[ -e $H/v2.mp4 ] && ok "#1 v2 in Mila's folder" "$(ls $H | tr '\n' ' ')" || bad "#1 v2 in folder" ""
sv $H/verdict.md $RUN PASS $D/step9-builds
OUT=$($R drive $RUN); expect "(f) PASS collected, lands in Review" "Run is complete through Step 10" "$OUT"
OUT=$($R status $RUN); expect "(e) headline Ready for Glam — freeze on" "HEADLINE: Ready for Glam — freeze on." "$OUT"
vid $D/step9-builds/v3.mp4 fake3
OUT=$($R status $RUN); expect "#1 build added after PASS is NOT covered" "Step 10 .*WAITING +new build since Mila's verdict" "$OUT"
expect "#1 headline no longer Ready for Glam" "HEADLINE: BLOCKED at Step 10" "$OUT"
OUT=$($R review-manifest); expect "#1 review shows not ready" "Not ready — waiting on Mila's check" "$OUT"
OUT=$($R drive $RUN); [ -e $H/v3.mp4 ] && ok "#1 v3 handed to Mila" "$(echo "$OUT"|grep -m1 Auto-handoff)" || bad "#1 v3 handed" "$OUT"
sv $H/verdict.md $RUN PASS $D/step9-builds
vid $D/step9-builds/v1.mp4 changed
OUT=$($R drive $RUN); OUT=$($R status $RUN); expect "#1 verdict written before a build changed does not cover the new version" "Step 10 .*WAITING +new build since Mila's verdict" "$OUT"
sv $H/verdict.md $RUN PASS $D/step9-builds; $R drive $RUN >/dev/null
OUT=$($R status $RUN); expect "#1 PASS on the exact current builds clears" "Step 10 .*CLEARED" "$OUT"
vid $D/step9-builds/v4.mp4 fake4; $R drive $RUN >/dev/null; printf 'verdict: PASS\nchecker: Mila Rice\n' > $H/verdict.md; $R drive $RUN >/dev/null
OUT=$($R status $RUN); expect "(f) PASS signed by someone else refused" "Step 10 .*INVALID.*not Mila's signed verdict" "$OUT"
rm $D/step9-builds/v4.mp4; rm -f $H/v4.mp4; sv $H/verdict.md $RUN PASS $D/step9-builds; $R drive $RUN >/dev/null
# ---------- #29 watch links
printf 'v1.mp4: https://drive.google.com/file/d/TESTID/view\n' > $D/step9-builds/links.md
$R review-manifest >/dev/null
grep -q '▶ Watch' $HOME/workspace/farm-runner/review-section.html && ok "#29 Watch link on card" "$(grep -o '<a href="[^"]*"' $HOME/workspace/farm-runner/review-section.html | head -1)" || bad "#29 watch link" ""
grep -q 'No watch link yet' $HOME/workspace/farm-runner/review-section.html && ok "#29 missing link says so" "No watch link yet — add it to links.md" || bad "#29 missing link msg" ""
grep -q '"watch_links"' $HOME/workspace/farm-runner/review-manifest.json && ok "#29 links in manifest JSON" "$(grep -m1 'drive.google' $HOME/workspace/farm-runner/review-manifest.json | sed 's/^ *//')" || bad "#29 json" ""
OUT=$($R handoff $RUN); echo "$OUT" | grep -q "links.md" && bad "#29 links.md not handed as a build" "$OUT" || ok "#29 links.md not handed as a build" "$(echo "$OUT"|head -1)"
OUT=$($R review-decision $RUN --decision approved; echo "exit $?"); expect "(f) review decision works after PASS (never posts)" "nothing posts" "$OUT"
# ---------- (e) freeze, #32
OUT=$($R check $RUN --to 11; echo "exit $?"); expect "(e) check --to 11 refused, freeze" "FREEZE-LOCKED" "$OUT"
OUT=$($R check $RUN --to 0); expect "#32 check --to 0 sane message" "not a step that can be checked" "$OUT"
grep -q "sync-review" "$(dirname "$0")/runner.py" && bad "#32 sync-review reference gone" "" || ok "#32 sync-review reference gone" "comment now names review-manifest"
OUT=$($R drive-all); expect "drive-all smoke test" "drive-all: drove" "$OUT"
# ---------- MASTER RULES FILE: farm-rules.json is the single source
RDIR="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(cd "$RDIR/.." && pwd)"
REAL_RULES="$ROOT/farm-rules.json"; [ -f "$RDIR/farm-rules.json" ] && REAL_RULES="$RDIR/farm-rules.json"
TMPR=$(mktemp -d)
python3 - "$REAL_RULES" "$TMPR/ten.json" "$TMPR/nana.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); d["numbers"]["max_spoken_words_per_line"]=10; json.dump(d,open(sys.argv[2],"w"))
d=json.load(open(sys.argv[1])); d["checks"]["person_words"].append("nana"); json.dump(d,open(sys.argv[3],"w"))
PY
printf 'CTA: it is linked below for you\nLINE 1: "Your feet hurt after every long double shift at work, girl."\nLINE 2: "Tap the orange cart."\n' > $S
OUT=$($R status $RUN); expect "RULES 11-word line passes under the real file (cap from JSON)" "Step 6 .*(WAITING|CLEARED)" "$OUT"
OUT=$(FARM_RULES=$TMPR/ten.json $R approve-script $RUN --by Mila); expect "RULES cap edited to 10 in the JSON -> same 11-word line fails, message says 10" "LINE 1 is 11 spoken words \(bar: 10 max\)" "$OUT"
printf 'Findings: x\nStory: For the nana who hosts every single Sunday dinner.\n' > $D/step2-scout/scout.md
OUT=$($R status $RUN); expect "RULES 'nana' not a person word in the real file -> fails" "Step 2 .*WAITING" "$OUT"
OUT=$(FARM_RULES=$TMPR/nana.json $R status $RUN); expect "RULES 'nana' added to person_words in the JSON -> passes" "Step 2 .*CLEARED" "$OUT"
printf 'Findings: x\nStory: Your feet hurt all week and you deserve a soft landing.\n' > $D/step2-scout/scout.md
OUT=$(FARM_RULES=$TMPR/missing.json $R status $RUN; echo "exit $?"); expect "RULES file missing -> runner stops, clear message, exit 4" "FARM RULES NOT FOUND.*exit 4" "$(echo "$OUT"|tr '\n' ' ')"
echo '{ broken' > $TMPR/broken.json
OUT=$(FARM_RULES=$TMPR/broken.json $R status $RUN; echo "exit $?"); expect "RULES file broken JSON -> runner stops, exit 4" "FARM RULES BROKEN.*exit 4" "$(echo "$OUT"|tr '\n' ' ')"
OUT=$($R check-rules --page "$ROOT/index.html"; echo "exit $?")
if echo "$OUT" | grep -q "exit 0"; then ok "RULES check-rules passes on the real rules file, runner and page" "$(echo "$OUT"|grep -m1 'check-rules: OK —' | cut -c1-120)"
else bad "RULES check-rules on the real files" "$(echo "$OUT"|tr '\n' ' ')"; fi
# ---------- ARCHIVE: nothing reads an archived book
cp "$RDIR/runner.py" $TMPR/runner_planted.py
printf 'BOOK = Path(__file__).parent / "RUNBOOK.md"\n' >> $TMPR/runner_planted.py
OUT=$($R check-rules --runner $TMPR/runner_planted.py --page "$ROOT/index.html"; echo "exit $?"); expect "ARCHIVE check-rules flags a planted RUNBOOK.md read in the runner" "reads 'RUNBOOK.md'.*exit 2" "$(echo "$OUT"|tr '\n' ' ')"
printf '<script>fetch("archive/merged-farm-playbook-v2.txt")</script> farm-rules.json farm-status.json' > $TMPR/page_planted.html
OUT=$($R check-rules --page $TMPR/page_planted.html; echo "exit $?"); expect "ARCHIVE check-rules flags a page that fetches an archived book" "loads an archived book.*exit 2" "$(echo "$OUT"|tr '\n' ' ')"
printf '<a href="https://github.com/x/y/tree/main/archive">Archive</a> farm-rules.json farm-status.json' > $TMPR/page_link.html
OUT=$($R check-rules --page $TMPR/page_link.html; echo "exit $?"); expect "ARCHIVE a visible LINK to the archive folder is allowed" "check-rules: OK.*exit 0" "$(echo "$OUT"|tr '\n' ' ')"
OUT=$($R sync-rules; echo "exit $?"); expect "ARCHIVE sync-rules retired, writes no book" "books are archived.*exit 0" "$(echo "$OUT"|tr '\n' ' ')"
# ---------- PLACEHOLDERS
python3 - "$REAL_RULES" "$TMPR/nope.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); d["laws"][0]["text"]+=" Planted {nope}."; json.dump(d,open(sys.argv[2],"w"))
PY
OUT=$(FARM_RULES=$TMPR/nope.json $R check-rules --page "$ROOT/index.html"; echo "exit $?"); expect "PLACEHOLDER a {nope} with no number is caught" "\{nope\} has no number.*exit 2" "$(echo "$OUT"|tr '\n' ' ')"
grep -q '{' $H/HANDOFF.md && bad "PLACEHOLDER HANDOFF.md fully filled (no { left)" "$(grep -m1 '{' $H/HANDOFF.md)" || ok "PLACEHOLDER HANDOFF.md fully filled (no { left)" "$(grep -m1 'spoken words' $H/HANDOFF.md | cut -c1-110)"
# ---------- LIVE STATUS FILE farm-status.json
$R approve-script $RUN --by Mila >/dev/null  # the RULES tests edited the script; re-record Mila's approval
rm -f $FARM_STATUS_OUT; $R status $RUN >/dev/null
python3 - $FARM_STATUS_OUT "$RUN" <<'PY' && ok "STATUS farm-status.json written with the exact schema" "keys ok" || bad "STATUS schema" "see above"
import json,sys
d=json.load(open(sys.argv[1]))
assert set(d)=={"generated_at","rules_version","freeze","runs"}, set(d)
assert d["freeze"]=="ON"
keys={"run_id","pick","model","mode","account","headline","state","open_step","open_step_name","needs","owner","steps","review_status","watch_links","is_test","handoffs","open_job"}
for r in d["runs"]:
    assert set(r)==keys, set(r)^keys
    assert r["state"] in ("READY","BLOCKED","STOPPED")
    for st in r["steps"]: assert set(st)=={"n","name","state","reason","agent"}
    for w in r["watch_links"]: assert set(w)=={"file","url"}
PY
OUT=$(python3 -c "import json;d=json.load(open('$FARM_STATUS_OUT'));r=[x for x in d['runs'] if x['run_id']=='$RUN'][0];print(r['state'],r['open_step'],r['is_test'],r['review_status'])")
expect "STATUS READY run has open_step null (TEST run flagged)" "^READY None True" "$OUT"
$R create --mode "Quick Tip" >/dev/null; RUN2=run-$(date +%F)-2
OUT=$($R status-export); expect "STATUS status-export writes the file" "farm-status.json written" "$OUT"
OUT=$(python3 -c "import json;d=json.load(open('$FARM_STATUS_OUT'));r=[x for x in d['runs'] if x['run_id']=='$RUN2'][0];print(r['state'],'|',r['open_step'],'|',r['owner'],'|',r['needs'])")
expect "STATUS BLOCKED run shows owner + what it needs" "^BLOCKED \| 2 \| TikTok Scout \| TikTok Scout — needs: the farm.s TikTok browser" "$OUT"
printf 'Findings: x\nStory: Your feet hurt and you deserve better.\n' > $HOME/workspace/farm-runs/$RUN2/steps/step2-scout/scout.md
printf 'product: TEST Mug\n' > $HOME/workspace/farm-runs/$RUN2/steps/step3-pick/pick.md
cp /tmp/fx_p.png $HOME/workspace/farm-runs/$RUN2/steps/step4-photo/p.png
$R record-match $RUN2 --checker Mila --grabber Mila --verdict MATCH >/dev/null
$R drive $RUN2 >/dev/null
OUT=$(python3 -c "import json;d=json.load(open('$FARM_STATUS_OUT'));r=[x for x in d['runs'] if x['run_id']=='$RUN2'][0];print(r['state'],'|',r['open_step'],'|',r['owner'])")
expect "STATUS STOPPED run (self-signed match) names step 5 and the checker" "^STOPPED \| 5 \| Photo Match checker" "$OUT"
[ ! -f "$ROOT/farm-status.json" ] && ok "STATUS tests never wrote into the repo" "FARM_STATUS_OUT honored" || bad "STATUS wrote into repo" "$ROOT/farm-status.json"
printf 'verdict: PASS\nchecker: Mila\n' >/dev/null
grep -q "MAJOR — must fix" $H/HANDOFF.md && grep -q "PASS BAR" $H/HANDOFF.md && grep -q "Farm laws (farm-rules.json" $H/HANDOFF.md && ok "RULES Mila's HANDOFF.md carries the scorecard + laws from the JSON" "$(grep -m1 "Mila's scorecard" $H/HANDOFF.md)" || bad "RULES handoff scorecard" "$(head -3 $H/HANDOFF.md)"
grep -qE '^(STORY_SPEC_WORDS|STORY_PERSON_WORDS|MODE_NAMES|USE_CLAIM_PATTERNS|SPOKEN_CTA_PATTERNS|STAGING_PATTERNS) = [\(\[]$' "$RDIR/runner.py" && bad "RULES no hard-coded rule lists left in runner.py" "" || ok "RULES no hard-coded rule lists left in runner.py" "all read from farm-rules.json"
rm -rf $TMPR
# ---------- Indigo's first real script (Nov 24 night): three rule breaks Glam caught by eye
RUN3=$($R create --mode "Get Ready With Me" | sed -n 's/^Run ID: //p')
D3=$HOME/workspace/farm-runs/$RUN3/steps
printf 'product: Turmeric + Honey Body Oil (Elowen Lab)\n' > $D3/step3-pick/pick.md
printf 'Clip 1: "Your skin has been dry all winter, sis."\nClip 2: "Turmeric and honey body oil right here on my vanity."\nShe holds the bottle and a drop lands on her hand.\nClip 3: "Tap the orange cart."\n' > $D3/step6-script/script.md
OUT=$($R approve-script $RUN3 --by Mila 2>&1)
expect "INDIGO script: approval refused" "APPROVAL REFUSED" "$OUT"
expect "INDIGO 'right here on my vanity' caught as a use/ownership claim" "\[use-claim\] LINE 2" "$OUT"
expect "INDIGO held bottle + drop on her hand caught as staging" "\[drawn-product\] script line 3" "$OUT"
expect "INDIGO no soft CTA up top caught" "\[no-cta\]" "$OUT"
printf 'References: approved styled image + the real listing photo\nC01 - 8 seconds, she smiles at the counter, product stationary.\n' > $D3/step8-package/package.md
OUT=$($R lint $RUN3 2>&1)
expect "INDIGO package with no caption fails" "no 'Caption:' in the package" "$OUT"
printf 'References: approved styled image + the real listing photo\nC01 - 8 seconds, product stationary.\nCaption: so cute right?\n#fyp #viral\n' > $D3/step8-package/package.md
OUT=$($R lint $RUN3 2>&1)
expect "caption with no product keyword fails" "doesn't name the product" "$OUT"
expect "caption with no soft CTA fails" "no soft CTA pointing below" "$OUT"
expect "caption with 2 hashtags fails" "2 hashtags" "$OUT"
expect "generic hashtags fail" "generic hashtags #fyp, #viral" "$OUT"
printf 'References: approved styled image + the real listing photo\nC01 - 8 seconds, product stationary.\nCaption: Turmeric honey body oil, linked below for your dry winter skin\n#turmericoil #bodyoil #dryskin #honeyskincare\n' > $D3/step8-package/package.md
OUT=$($R lint $RUN3 2>&1)
expect "fixed caption passes" "package passes" "$OUT"
printf 'CTA: it is linked below for you\nClip 1: "Your skin has been dry all winter, sis."\nClip 2: "This one sits right there on the counter."\nThe bottle stays on the counter, no hands on it.\nClip 3: "Tap the orange cart."\n' > $D3/step6-script/script.md
OUT=$($R status $RUN3 2>&1)
expect "INDIGO script rewritten to the rules passes the check" "Step 6 +Script +(WAITING|BLOCKED).*(passing the script check|earlier gate)" "$OUT"
OUT=$($R approve-script $RUN3 --by Mila 2>&1)
expect "rewritten script takes Mila's approval" "Recorded Mila's script approval" "$OUT"
# ---------- FULL CHAIN TEST (Glam's order: Scout → Shop Agent → Story → Casting → Video → Mila → Glam; nothing posts)
CH=$(mktemp -d)
OUT=$($R create --mode "Get Ready With Me" 2>&1); RC=$(echo "$OUT" | sed -n 's/^Run ID: //p'); C=$HOME/workspace/farm-runs/$RC; CS=$C/steps
expect "CHAIN create opens the Scout's job" "job opened for TikTok Scout|Chain: job opened for TikTok Scout" "$OUT"
[ -f $CS/step2-scout/JOB.md ] && grep -q "Your job" $CS/step2-scout/JOB.md && ok "CHAIN Scout JOB.md written from farm-rules.json" "$(grep -m1 '^# JOB' $CS/step2-scout/JOB.md)" || bad "CHAIN Scout JOB.md" ""
OUT=$($R jobs 2>&1); expect "CHAIN jobs lists the open Scout job" "TikTok Scout — $RC Step 2" "$OUT"
python3 -c "import json,os;d=json.load(open(os.path.join(os.path.dirname('$FARM_STATUS_OUT'),'farm-jobs.json')));assert any(j['run_id']=='$RC' and j['agent']=='TikTok Scout' for j in d['jobs'])" && ok "CHAIN farm-jobs.json lists the Scout job" "farm-jobs.json" || bad "CHAIN farm-jobs.json" ""
OUT=$(python3 -c "import json;d=json.load(open('$FARM_STATUS_OUT'));r=[x for x in d['runs'] if x['run_id']=='$RC'][0];print(r['open_job']['agent'],'|',r['state'],'|',r['owner'])"); expect "CHAIN status: open_job = TikTok Scout, BLOCKED until it submits" "^TikTok Scout \| BLOCKED \| TikTok Scout" "$OUT"
printf 'Findings: TEST — slides trending in Shop best sellers (test data)\nStory: Your feet ache after a long shift and you deserve soft.\n' > $CH/scout.md
OUT=$($R submit $RC --step 2 --by "Story Agent" --file $CH/scout.md; echo "exit $?"); expect "CHAIN wrong agent refused (--by must be the step's agent)" "SUBMIT REFUSED — Step 2 belongs to TikTok Scout.*exit 2|exit 2" "$(echo "$OUT"|tr '\n' ' ')"
OUT=$($R submit $RC --step 6 --by "Story Agent" --file $CH/scout.md; echo "exit $?"); expect "CHAIN out-of-order submit refused" "isn't the open job" "$OUT"
OUT=$($R submit $RC --step 2 --by "TikTok Scout" --file $CH/scout.md); expect "CHAIN Scout → Shop Agent" "Handed to TikTok Shop Agent \(Step 3\)" "$OUT"
grep -q "steps/step2-scout/scout.md" $CS/step3-pick/JOB.md && ok "CHAIN Shop job reads the Scout's file (with sha256)" "$(grep -m1 'scout.md' $CS/step3-pick/JOB.md)" || bad "CHAIN Shop job inputs" ""
printf 'product: TEST Cloud Slides\nlisting: TEST-0001 (test data)\n' > $CH/pick.md
OUT=$($R submit $RC --step 3 --by "TikTok Shop Agent" --file $CH/pick.md); expect "CHAIN pick → Shop Agent grabs the photo (Step 4)" "Handed to TikTok Shop Agent \(Step 4\)" "$OUT"
cp /tmp/fx_p.png $CH/listing.png
OUT=$($R submit $RC --step 4 --by "TikTok Shop Agent" --file $CH/listing.png); expect "CHAIN photo → Photo Match checker" "Handed to Photo Match checker \(Step 5\)" "$OUT"
OUT=$($R submit $RC --step 5 --by "Mila" --file $CH/pick.md; echo "exit $?"); expect "CHAIN Step 5 only via record-match" "record-match" "$OUT"
$R record-match $RC --checker Mila --grabber "TikTok Shop Agent" --verdict MATCH >/dev/null
[ -f $CS/step6-script/JOB.md ] && grep -q "scout.md" $CS/step6-script/JOB.md && grep -q "step4-photo/listing.png" $CS/step6-script/JOB.md && ok "CHAIN Story job opened with the story sentence + listing photo as inputs" "$(grep -c sha256 $CS/step6-script/JOB.md) inputs with sha256" || bad "CHAIN Story job inputs" "$(cat $CS/step6-script/JOB.md 2>/dev/null | head -5)"
printf 'CTA: it is linked below for you\nLINE 1: "Your feet hurt after every long shift."\nShe holds the bottle up to the camera.\nLINE 2: "Tap the orange cart."\n' > $CH/script-bad.md
OUT=$($R submit $RC --step 6 --by "Story Agent" --file $CH/script-bad.md; echo "exit $?"); expect "CHAIN held-bottle script SENT BACK to the Story Agent" "SENT BACK to Story Agent" "$OUT"
grep -q "SENT BACK" $CS/step6-script/JOB.md && grep -q "puts the product itself in a shot" $CS/step6-script/JOB.md && ok "CHAIN findings written at the top of the Story Agent's JOB.md" "$(sed -n 3p $CS/step6-script/JOB.md | cut -c1-100)" || bad "CHAIN sent-back JOB.md" ""
OUT=$(python3 -c "import json;d=json.load(open('$FARM_STATUS_OUT'));r=[x for x in d['runs'] if x['run_id']=='$RC'][0];print(r['state'],'|',r['open_job']['agent'],'|',len(r['open_job']['sent_back']))"); expect "CHAIN status shows STOPPED, sent back to Story Agent" "^STOPPED \| Story Agent \| [1-9]" "$OUT"
printf 'CTA: it is linked below for you\nLINE 1: "Your feet hurt after every long shift."\nThe slides sit on the counter, no hands on them.\nLINE 2: "Tap the orange cart."\n' > $CH/script.md
OUT=$($R submit $RC --step 6 --by "Story Agent" --file $CH/script.md); expect "CHAIN corrected script passes → Mila (not Glam)" "Handed to Mila \(Step 6\)" "$OUT"
OUT=$($R approve-script $RC --by Glam 2>&1; echo "exit $?"); expect "FLOW Glam is not asked before the video: approve-script --by Glam refused" "only Mila approves the script.*exit 2" "$(echo "$OUT"|tr '\n' ' ')"
OUT=$($R approve-script $RC --by Mila --send-back "Line 1 needs to name who it is for"); expect "FLOW Mila sends the script back → Story Agent" "next is Story Agent \(Step 6\)" "$OUT"
grep -q "Mila sent the script back: Line 1 needs to name who it is for" $CS/step6-script/JOB.md && ok "FLOW Mila's notes at the top of the Story Agent's JOB.md" "$(sed -n 2p $CS/step6-script/JOB.md)" || bad "FLOW Mila notes in JOB.md" ""
printf 'CTA: it is linked below for you\nLINE 1: "Your feet hurt after every long shift, nurses."\nThe slides sit on the counter, no hands on them.\nLINE 2: "Tap the orange cart."\n' > $CH/script.md
OUT=$($R submit $RC --step 6 --by "Story Agent" --file $CH/script.md); expect "FLOW fixed script → back to Mila" "Handed to Mila \(Step 6\)" "$OUT"
OUT=$(python3 -c "import json;d=json.load(open('$FARM_STATUS_OUT'));r=[x for x in d['runs'] if x['run_id']=='$RC'][0];print(r['open_job'],'|',r['owner'],'|',r['needs'])"); expect "CHAIN Mila gate: open job is Mila's, not Glam's" "'agent': 'Mila'.*\| Mila" "$OUT"
OUT=$($R approve-script $RC --by Mila); expect "CHAIN Mila's script approval → Casting / Image Agent" "next is Casting / Image Agent \(Step 7\)" "$OUT"
cp /tmp/fx_p.png $CH/model-uploaded.png
OUT=$($R submit $RC --step 7 --by "Casting / Image Agent" --file $CH/model-uploaded.png); expect "CHAIN model photo → Mila (not Glam)" "Handed to Mila \(Step 7\)" "$OUT"
OUT=$($R approve-image $RC --by Mila); expect "CHAIN Mila's image approval → package job, video next with no Glam stop" "next is Story Agent \+ Video Agent \(Step 8\)" "$OUT"
printf 'References: approved model photo + the real listing photo\nC01 - 8 seconds, she smiles at the counter, product stationary.\n' > $CH/package-nocap.md
OUT=$($R submit $RC --step 8 --by "Story Agent" --file $CH/package-nocap.md; echo "exit $?"); expect "CHAIN package without a caption SENT BACK" "SENT BACK to Story Agent \+ Video Agent" "$OUT"
printf 'References: approved model photo + the real listing photo\nC01 - 8 seconds, she smiles at the counter, product stationary.\nCaption: Cloud Slides linked below for your tired feet\n#cloudslides #slides #comfyslides\n' > $CH/package.md
OUT=$($R submit $RC --step 8 --by "Video Agent" --file $CH/package.md); expect "CHAIN package with caption passes → Video Agent" "Handed to Video Agent \(Step 9\)" "$OUT"
vid $CH/build-1.mp4 "TEST build 1"
OUT=$($R submit $RC --step 9 --by "Indigo" --file $CH/build-1.mp4); expect "CHAIN build → Mila" "Handed to Mila \(Step 10\)" "$OUT"
[ -f $HOME/workspace/farm-qc-handoff/$RC/build-1.mp4 ] && [ -f $CS/step10-qc/JOB.md ] && ok "CHAIN build handed to Mila's QC folder + her JOB.md" "farm-qc-handoff/$RC/build-1.mp4" || bad "CHAIN Mila handoff" ""
OUT=$(python3 -c "import json;d=json.load(open('$FARM_STATUS_OUT'));r=[x for x in d['runs'] if x['run_id']=='$RC'][0];print(r['open_job']['agent'],'|',r['owner'])"); expect "CHAIN status open_job = Mila" "^Mila \| Mila" "$OUT"
sv $CH/verdict.md $RC PASS $CS/step9-builds
OUT=$($R submit $RC --step 10 --by "Mila" --file $CH/verdict.md); expect "CHAIN Mila's PASS → Glam's final review" "Handed to Glam: final review" "$OUT"
OUT=$($R status $RC); expect "CHAIN ends at Ready for Glam — freeze on" "HEADLINE: Ready for Glam — freeze on\." "$OUT"
OUT=$($R post $RC 2>&1; echo "exit $?"); expect "CHAIN there is no post command (nothing posts)" "invalid choice.*exit 2|exit 2" "$(echo "$OUT"|tr '\n' ' ')"
python3 - $C/handoffs.jsonl <<'PY' && ok "CHAIN handoffs.jsonl has every hop in order, with inputs + sha256" "hops ok" || bad "CHAIN handoffs order" "see above"
import json,sys
H=[json.loads(l) for l in open(sys.argv[1])]
want=[("Start a Run","TikTok Scout","handed off"),("TikTok Scout","TikTok Shop Agent","handed off"),
("TikTok Shop Agent","TikTok Shop Agent","handed off"),("TikTok Shop Agent","Photo Match checker","handed off"),
("Mila","Story Agent","handed off"),("Story Agent","Story Agent","sent back"),("Story Agent","Mila","waiting on Mila"),("Mila","Story Agent","sent back"),("Story Agent","Mila","waiting on Mila"),
("Mila","Casting / Image Agent","handed off"),("Casting / Image Agent","Mila","waiting on Mila"),
("Mila","Story Agent + Video Agent","handed off"),("Story Agent","Story Agent + Video Agent","sent back"),
("Video Agent","Video Agent","handed off"),("Indigo","Mila","waiting on Mila"),("Mila","Glam","waiting on Glam")]
got=[(h["from"],h["to"],h["result"]) for h in H]
assert got==want, "\n".join(map(str,got))
for h in H:
    assert set(h)=={"at","from","to","step","what","inputs","output","result"}, h
for h in H[1:]:
    assert h["inputs"] and all(len(i["sha256"])==64 for i in h["inputs"]), h
PY
python3 -c "
import json;[print(f\"  {i:2}. {h['from']} → {h['to']} (Step {h['step'] or 'review'}) — {h['result']}\") for i,h in enumerate((json.loads(l) for l in open('$C/handoffs.jsonl')),1)]" > /tmp/fx_hops.txt
# ---------- Glam's one ruling, on the finished video: Redo with notes, or Approve (freeze stays on)
OUT=$($R review-decision $RC --decision redo 2>&1; echo "exit $?"); expect "REVIEW redo without notes refused" "REDO REFUSED.*exit 2" "$(echo "$OUT"|tr '\n' ' ')"
OUT=$($R review-decision $RC --decision redo --notes "Make her smile more in clip 2 and slow the last line" 2>&1); expect "REVIEW Redo sends the video back to the Video Agent" "back to the Video Agent" "$OUT"
[ ! -f $CS/step9-builds/build-1.mp4 ] && [ -f $C/redo/redo-1/builds/build-1.mp4 ] && [ -f $C/redo/redo-1/qc/mila-verdict.md ] && ok "REVIEW old build + Mila's verdict kept in redo/redo-1" "redo/redo-1/" || bad "REVIEW redo archive" "$(ls -R $C/redo 2>&1|head)"
grep -q "Glam asked for a redo (#1): Make her smile more in clip 2" $CS/step9-builds/JOB.md && ok "REVIEW Glam's notes at the top of the Video Agent's JOB.md" "$(sed -n 2p $CS/step9-builds/JOB.md)" || bad "REVIEW notes in JOB.md" "$(head -3 $CS/step9-builds/JOB.md)"
OUT=$(python3 -c "import json;d=json.load(open('$HOME/workspace/farm-runner/review-manifest.json'));e=[x for x in d['entries'] if x['run_id']=='$RC'][0];print(e['review_status'],'|',e['glam_notes'])"); expect "REVIEW page list shows the redo with her notes" "^Redo — being rebuilt with Glam's notes \| Make her smile" "$OUT"
vid $CH/build-2.mp4 "TEST build 2"
OUT=$($R submit $RC --step 9 --by "Indigo" --file $CH/build-2.mp4); expect "REVIEW rebuild → Mila checks again" "Handed to Mila \(Step 10\)" "$OUT"
sv $CH/verdict2.md $RC PASS $CS/step9-builds
OUT=$($R submit $RC --step 10 --by "Mila" --file $CH/verdict2.md); expect "REVIEW Mila's PASS on the rebuild → Glam's final review" "Handed to Glam: final review" "$OUT"
printf '[{"run_id":"%s","decision":"approved","notes":"Love it","at":"2026-11-25T01:00:00Z"}]' $RC > $CH/taps.json
OUT=$($R review-apply --file $CH/taps.json 2>&1); expect "REVIEW Approve tap from the review page is applied" "APPROVAL.*nothing posts" "$(echo "$OUT"|tr '\n' ' ')"
OUT=$($R review-apply --file $CH/taps.json 2>&1); expect "REVIEW the same tap is applied only once" "already applied" "$OUT"
OUT=$(python3 -c "import json;d=json.load(open('$HOME/workspace/farm-runner/review-manifest.json'));e=[x for x in d['entries'] if x['run_id']=='$RC'][0];print(e['review_status'])"); expect "REVIEW status: Approved — ready to post, freeze on" "^Approved — ready to post \(freeze on\)" "$OUT"
OUT=$($R status $RC); expect "REVIEW freeze still on after approval" "Step 11 +Caption & Post +FROZEN" "$OUT"
rm -rf $CH
echo; echo "CHAIN HOPS (test data):"; cat /tmp/fx_hops.txt
# ---------- Glam's Nov 24 calls: retire the 4 first-person modes; the retired agent stays off the farm
ROOT2="$(cd "$(dirname "$0")/.." && pwd)"
OUT=$(python3 -c "import json;d=json.load(open('$ROOT2/farm-rules.json'));m=d['form']['modes'];r=d['form']['retired_modes']['modes'];print(len(m),d['numbers']['modes'],[x for x in r if x in m])")
expect "retired modes are off the farm (12 modes, none of the 4 left)" "^12 12 \[\]" "$OUT"
sc "retired mode name still fails as an opener" 'CTA: linked below\nLINE 1: "My honest take for you girls."\n' "INVALID"
NM="N""ora"; TMPN=$(mktemp -d); cp -r "$ROOT2/farm-runner" "$ROOT2/index.html" "$ROOT2/farm-rules.json" "$TMPN/"; rm -rf "$TMPN/farm-runner/__pycache__"
OUT=$(python3 "$TMPN/farm-runner/runner.py" check-rules 2>&1; echo "exit $?"); expect "clean farm passes the banned-agent check" "check-rules: OK" "$OUT"
echo "Ask $NM to help" >> "$TMPN/index.html"
OUT=$(python3 "$TMPN/farm-runner/runner.py" check-rules 2>&1; echo "exit $?"); expect "a planted mention of the retired agent is caught" "index.html mentions $NM" "$OUT"
rm -rf "$TMPN"
# ---------- Glam's locked rule (Nov 25): your step only, hand off automatically, or BLOCKED
RL=$($R create --mode "Get Ready With Me" | sed -n 's/^Run ID: //p'); JL=$HOME/workspace/farm-runs/$RL/steps/step2-scout/JOB.md
grep -q "LOCKED: Locked to your own step, then hand off" $JL && grep -q "report BLOCKED" $JL && ok "LOCKED rule at the top of the Scout's JOB.md" "$(grep -m1 LOCKED $JL)" || bad "LOCKED rule in JOB.md" "$(head -5 $JL)"
OUT=$(python3 -c "import json;d=json.load(open('$ROOT2/farm-rules.json'));print(all('own-step-handoff' in a['laws'] for a in d['agents']), len(d['agents']))"); expect "LOCKED rule is on every agent" "^True 9" "$OUT"
TMPL=$(mktemp -d); cp -r "$ROOT2/farm-runner" "$ROOT2/index.html" "$ROOT2/farm-rules.json" "$TMPL/"; rm -rf "$TMPL/farm-runner/__pycache__"
python3 - "$TMPL/farm-rules.json" <<'PY2'
import json,sys;p=sys.argv[1];d=json.load(open(p));d['agents'][0]['laws'].remove('own-step-handoff');json.dump(d,open(p,'w'))
PY2
OUT=$(python3 "$TMPL/farm-runner/runner.py" check-rules 2>&1; echo "exit $?"); expect "check-rules fails if an agent loses the locked rule" "missing Glam's locked rule" "$OUT"
rm -rf "$TMPL"

# ---------- Glam, Nov 25 (2026-11-25f): every-product rules + enforcement
# A fresh run to prove each new rule stops what it should.
OUT=$($R create --mode "Get Ready With Me" 2>&1); RN=$(echo "$OUT" | sed -n 's/^Run ID: //p'); N=$HOME/workspace/farm-runs/$RN/steps
printf 'Findings: x\nStory: Your feet hurt all week and you deserve a soft landing.\n' > $N/step2-scout/scout.md
printf 'product: TEST Scalp Oil\nlisting: test\n' > $N/step3-pick/pick.md
$R attach-photo $RN /tmp/fx_p.png --by Indigo >/dev/null; $R record-match $RN --checker Mila --grabber Indigo --verdict MATCH >/dev/null
SN=$N/step6-script/script.md
scn(){ printf "%b" "$2" > $SN; OUT=$($R status $RN | grep 'Step 6 '); expect "$1" "$3" "$OUT"; }
scn "EVERY run 1's 'glide across the back of my hand' now passes (use is allowed)" 'CTA: linked below for you\nLINE 1: "You took care of everybody today. This minute is yours."\nLINE 2: "Watch it glide across the back of my hand."\n' "WAITING.*passing"
scn "EVERY run 2's growth line fails" 'CTA: linked below for you\nLINE 1: "On your feet all day for everybody else, tonight is yours."\nLINE 2: "This hair growth oil sits by the sink."\n' "INVALID.*health-claim"
scn "EVERY growth claim in a hashtag fails" 'CTA: linked below for you\nCaption: Scalp oil for your wash day, linked below #scalpoil #hairgrowth #washday\nLINE 1: "Your wash day deserves five quiet minutes."\n' "INVALID.*health-claim"
scn "EVERY before-and-after spoken fails" 'CTA: linked below for you\nLINE 1: "Your wash day deserves five quiet minutes."\nLINE 2: "Before and after, you can see it."\n' "INVALID.*before-after"
scn "EVERY hair flip reveal in directions fails" 'CTA: linked below for you\nLINE 1: "Your wash day deserves five quiet minutes."\nThen a hair flip to show the after.\n' "INVALID.*before-after"
scn "EVERY bottle held in a direction fails" 'CTA: linked below for you\nLINE 1: "Your wash day deserves five quiet minutes."\nShe holds the bottle up to the camera.\n' "INVALID.*drawn-product"
scn "EVERY clean use script passes" 'CTA: linked below for you\nLINE 1: "Your wash day deserves five quiet minutes."\nShe works the oil into her scalp with her fingertips, product off frame.\nLINE 2: "Tap the orange cart."\n' "WAITING.*passing"
printf 'verdict: APPROVE\nchecker: Mila\napproved_by: Mila\n' > $N/step6-script/mila-script-approval.md
OUT=$($R status $RN | grep 'Step 6 '); expect "EVERY a typed 'approved_by: Mila' does not clear Step 6" "WAITING.*not Mila's signed verdict" "$OUT"
rm $N/step6-script/mila-script-approval.md
OUT=$(MILA_SIGNING_KEY=/nonexistent $R approve-script $RN --by Mila; echo "exit $?"); expect "EVERY --by Mila without Mila's key is refused" "count only from her signed verdict file.*exit 2" "$(echo "$OUT"|tr '\n' ' ')"
$R mila-sign --run $RN --step 6 --verdict APPROVE --file $SN --out /tmp/fx/v6.md >/dev/null
OUT=$(MILA_SIGNING_KEY=/nonexistent $R approve-script $RN --verdict-file /tmp/fx/v6.md); expect "EVERY Mila's signed verdict file clears Step 6 (no key needed to check it)" "next is Casting" "$OUT"
$R mila-sign --run run-other-1 --step 6 --verdict APPROVE --file $SN --out /tmp/fx/v6x.md >/dev/null
OUT=$($R approve-script $RN --verdict-file /tmp/fx/v6x.md; echo "exit $?"); expect "EVERY a signed verdict for another run is refused" "for run-other-1 Step 6, not this run.*exit 2" "$(echo "$OUT"|tr '\n' ' ')"
OUT=$(FARM_LIVE_RULES_URL=file:///tmp/fx/old-rules.json $R create --mode "Get Ready With Me" 2>&1; echo "exit $?")
python3 -c "import json;d=json.load(open('$ROOTF/farm-rules.json'));d['version']='2026-11-24-old';json.dump(d,open('/tmp/fx/old-rules.json','w'))"
OUT=$(FARM_LIVE_RULES_URL=file:///tmp/fx/old-rules.json $R create --mode "Get Ready With Me" 2>&1; echo "exit $?"); expect "EVERY a run refuses to start when this copy differs from the live rules" "START A RUN REFUSED.*live farm is version 2026-11-24-old.*exit 2" "$(echo "$OUT"|tr '\n' ' ')"
OUT=$(FARM_LIVE_RULES_URL=file:///tmp/fx/nothing-here.json $R submit $RN --step 7 --by "Casting / Image Agent" --file /tmp/fx_p.png 2>&1; echo "exit $?"); expect "EVERY can't reach the live rules = BLOCKED, nothing moves" "BLOCKED: can't reach the live farm rules.*exit 2" "$(echo "$OUT"|tr '\n' ' ')"
python3 - "$ROOTF/farm-runner" <<'PY' && ok "EVERY clip length is read from the mp4 itself" "34 / 8 / 5 seconds" || bad "EVERY clip length read" ""
import sys;sys.path.insert(0,sys.argv[1]);sys.argv=['x']
import runner as r
assert round(r.mp4_seconds('/tmp/fx_base34.mp4'))==34 and round(r.mp4_seconds('/tmp/fx_base8.mp4'))==8
assert r.build_length_problem('/tmp/fx_base34.mp4') is None and r.build_length_problem('/tmp/fx_base8.mp4') is None
assert 'runs 5.0 seconds' in r.build_length_problem('/tmp/fx_base5.mp4')
PY
vid /tmp/fx/short.mp4 short /tmp/fx_base5.mp4
cp /tmp/fx/short.mp4 $N/step9-builds/short.mp4
OUT=$($R status $RN | grep 'Step 9 '); expect "EVERY a 5-second clip fails before Mila sees it" "INVALID.*clip length check FAILS before Mila.*5.0 seconds" "$OUT"
# Glam, Nov 25: every step publishes to the Live Run Board, and a failed publish is loud.
PB=/tmp/fx_pub; rm -rf $PB; mkdir -p $PB
git init -q --bare $PB/origin.git
git clone -q $PB/origin.git $PB/farm 2>/dev/null
cp -r "$ROOTF/farm-runner" "$ROOTF/farm-rules.json" "$ROOTF/index.html" $PB/farm/
OUT=$(cd $PB && env -u FARM_NO_PUBLISH HOME=$PB/home python3 $PB/farm/farm-runner/runner.py create --mode "Get Ready With Me" 2>&1)
expect "STATUS a new run publishes to the Live Run Board" "Status published to the Live Run Board" "$OUT"
OUT=$(git --git-dir=$PB/origin.git show farm-status:farm-status.json 2>&1 | python3 -c "import json,sys;d=json.load(sys.stdin);print(len(d['runs']),d['runs'][0]['open_step'])" 2>&1)
expect "STATUS the farm-status branch holds the run, open at Step 2" "^1 2$" "$OUT"
OUT=$(git --git-dir=$PB/origin.git ls-tree --name-only farm-status | tr '\n' ' ')
expect "STATUS the farm-status branch holds the two status files and the shared runs" "^farm-jobs.json farm-status.json runs $" "$OUT"
RID=$(git --git-dir=$PB/origin.git ls-tree --name-only farm-status:runs | head -1)
OUT=$(git --git-dir=$PB/origin.git show farm-status:runs/$RID/config.json | python3 -c "import json,sys;print(json.load(sys.stdin)['mode'])" 2>&1)
expect "STATUS the whole run folder is shared on GitHub" "Get Ready With Me" "$OUT"
# A second agent on another computer gets the run before it does anything.
git clone -q $PB/origin.git $PB/farm2 2>/dev/null; cp -r "$ROOTF/farm-runner" "$ROOTF/farm-rules.json" "$ROOTF/index.html" $PB/farm2/
OUT=$(cd $PB && env -u FARM_NO_PUBLISH HOME=$PB/home2 python3 $PB/farm2/farm-runner/runner.py status $RID 2>&1)
expect "SHARED a second agent's computer pulls the run down first" "Step 2" "$OUT"
[ -f $PB/home2/workspace/farm-runs/$RID/config.json ] && ok "SHARED run folder arrived on the second computer" "$RID" || bad "SHARED run folder missing on the second computer" ""
[ -d $PB/home2/workspace/farm-runs/$RID/steps/step3-pick ] && [ -d $PB/home2/workspace/farm-runs/$RID/steps/step10-qc ] && ok "SHARED empty step folders come back after a sync" "step3-pick" || bad "SHARED empty step folders missing after sync" "$(ls $PB/home2/workspace/farm-runs/$RID/steps)"
echo "scout notes from computer 2" > $PB/home2/workspace/farm-runs/$RID/steps/step2-scout/note2.txt
OUT=$(cd $PB && env -u FARM_NO_PUBLISH HOME=$PB/home2 python3 $PB/farm2/farm-runner/runner.py status-export 2>&1)
OUT=$(cd $PB && env -u FARM_NO_PUBLISH HOME=$PB/home python3 $PB/farm/farm-runner/runner.py status-export 2>&1)
[ -f $PB/home/workspace/farm-runs/$RID/steps/step2-scout/note2.txt ] && ok "SHARED work done on computer 2 reaches computer 1" "note2.txt" || bad "SHARED work from computer 2 did not arrive" "$OUT"
echo "edit A" > $PB/home/workspace/farm-runs/$RID/steps/step2-scout/clash.txt
echo "edit B" > $PB/home2/workspace/farm-runs/$RID/steps/step2-scout/clash.txt
(cd $PB && env -u FARM_NO_PUBLISH HOME=$PB/home python3 $PB/farm/farm-runner/runner.py status-export >/dev/null 2>&1)
OUT=$(cd $PB && env -u FARM_NO_PUBLISH HOME=$PB/home2 python3 $PB/farm2/farm-runner/runner.py status-export 2>&1)
expect "SHARED the same run changed on two computers is a loud conflict, nothing overwritten" "RUN CONFLICT|changed on the shared farm" "$(echo "$OUT"|tr '\n' ' ')"
OUT=$(cat $PB/home2/workspace/farm-runs/$RID/steps/step2-scout/clash.txt); expect "SHARED the conflicting copy was kept, not overwritten" "^edit B$" "$OUT"
rm -f $PB/home/workspace/farm-runs/$RID/steps/step2-scout/clash.txt $PB/home2/workspace/farm-runs/$RID/steps/step2-scout/clash.txt
echo x > $PB/home/workspace/farm-runs/$(ls $PB/home/workspace/farm-runs|head -1)/steps/step2-scout/more.txt
OUT=$(cd $PB && env -u FARM_NO_PUBLISH HOME=$PB/home python3 $PB/farm/farm-runner/runner.py status-export 2>&1)
expect "STATUS a second publish stacks on the first" "Status published to the Live Run Board" "$OUT"
N2=$(git --git-dir=$PB/origin.git rev-list --count farm-status); expect "STATUS branch history kept (2+ commits)" "^([2-9]|[1-9][0-9])$" "$N2"
mv $PB/origin.git $PB/gone.git
OUT=$(cd $PB && env -u FARM_NO_PUBLISH HOME=$PB/home python3 $PB/farm/farm-runner/runner.py status-export 2>&1)
expect "STATUS a failed publish says so out loud, never silent" "STATUS NOT PUBLISHED" "$OUT"
mv $PB/gone.git $PB/origin.git
grep -q "farm-status/farm-status.json\|refs/heads/farm-status\|commits/farm-status" "$ROOTF/index.html" && ok "STATUS live page reads the farm-status branch" "index.html" || bad "STATUS live page reads the farm-status branch" "not found"
grep -q "STATUS COULDN.T LOAD\|Live Run Board couldn" "$ROOTF/index.html" && ok "STATUS live page shows an error when it can't load" "index.html" || bad "STATUS live page error message" "not found"
grep -q 'id="autoRunBtn" href="https://github.com/nakeymasi-coder/futuristic-3d-tiktok-shop-farm/actions/workflows/start-run.yml"' "$ROOTF/index.html" && ok "START the page button opens the real Start Run on GitHub" "index.html" || bad "START button does not open the real Start Run" ""
! grep -q "finishAutoRun\|walkStepsEl" "$ROOTF/index.html" && ok "START the fake run animation is gone" "index.html" || bad "START fake animation still on the page" ""
grep -q "workflow_dispatch" "$ROOTF/.github/workflows/start-run.yml" && grep -q 'runner.py create' "$ROOTF/.github/workflows/start-run.yml" && grep -q "contents: write" "$ROOTF/.github/workflows/start-run.yml" && ok "START the GitHub workflow creates the run and may publish it" "start-run.yml" || bad "START workflow" ""
grep -q 'class="btn btn-pink mini lane-real" href="https://github.com/nakeymasi-coder/futuristic-3d-tiktok-shop-farm/actions/workflows/start-run.yml"' "$ROOTF/index.html" && ok "LANES the Shop lane starts the real run" "index.html" || bad "LANES Shop lane" ""
[ "$(grep -c 'Start this run →\|Start a posting run →' "$ROOTF/index.html")" = 0 ] && ok "LANES no lane button claims to start a run it doesn't" "index.html" || bad "LANES a lane button still claims to start a run" ""
[ "$(grep -c 'Write a draft prompt (no run)' "$ROOTF/index.html")" = 5 ] && ok "LANES the five lanes without run steps say draft only" "5 buttons" || bad "LANES draft labels" ""
grep -q 'window.open("https://github.com/nakeymasi-coder/futuristic-3d-tiktok-shop-farm/actions/workflows/start-run.yml"' "$ROOTF/index.html" && ! grep -q 'Product-to-Post run added to your queue' "$ROOTF/index.html" && ok "LANES Product-to-Post opens the real run, no queue draft" "index.html" || bad "LANES Product-to-Post" ""
grep -q 'product:' "$ROOTF/.github/workflows/start-run.yml" && grep -q -- '--pick "$PRODUCT"' "$ROOTF/.github/workflows/start-run.yml" && ok "LANES the workflow takes the product for Product-to-Post" "start-run.yml" || bad "LANES workflow product input" ""
! grep -q 'status: "Waiting' "$ROOTF/index.html" && grep -q 'pill.textContent = "Draft — not a run"' "$ROOTF/index.html" && grep -q "var queue = \[\];" "$ROOTF/index.html" && ok "QUEUE drafts never show a run's step status, and no sample draft is seeded" "index.html" || bad "QUEUE drafts still look like runs" ""
grep -q "UP NOW" "$ROOTF/index.html" && ok "BOARD agents light up from the real status" "index.html" || bad "BOARD agent lights" ""

# Glam, Nov 25: each agent is its own session; Mila's key only in her session.
SG=/tmp/fx_sess; rm -rf $SG; mkdir -p $SG/home
Rn(){ env -u FARM_TEST_MODE HOME=$SG/home python3 "$ROOTF/farm-runner/runner.py" "$@"; }
Rn create --mode "Get Ready With Me" >/dev/null 2>&1
SR=$(ls $SG/home/workspace/farm-runs | head -1)
printf 'Scout notes: the trends.\nStory: For grown ladies who give everyone else their evenings, this is a little scalp-care moment that is just theirs.\n' > $SG/scout.md
OUT=$(Rn submit $SR --step 2 --by "TikTok Scout" --file $SG/scout.md 2>&1; echo "exit $?"); expect "SESSION a hand-in without the agent's own session is refused" "SUBMIT REFUSED.*names the agent's own id.*exit 2" "$(echo "$OUT"|tr '\n' ' ')"
OUT=$(Rn submit $SR --step 2 --by "TikTok Scout" --file $SG/scout.md --session session_01SCOUTAAAAAAA 2>&1); expect "SESSION the Scout's own session hands in" "checks passed|Handed to" "$OUT"
printf 'product: Test Oil\nlisting ID: 123\n' > $SG/pick.md
OUT=$(Rn submit $SR --step 3 --by "TikTok Shop Agent" --file $SG/pick.md --session session_01SCOUTAAAAAAA 2>&1; echo "exit $?"); expect "SESSION one session can't play a second agent" "already acted as TikTok Scout.*One session, one role.*exit 2" "$(echo "$OUT"|tr '\n' ' ')"
OUT=$(Rn submit $SR --step 3 --by "TikTok Shop Agent" --file $SG/pick.md --session session_01SHOPBBBBBBBB 2>&1); expect "SESSION the Shop Agent's own session hands in" "checks passed|Handed to" "$OUT"
OUT=$(Rn proof $SR 2>&1); expect "PROOF lists a different session per step" "OK — 2 different id" "$(echo "$OUT"|tr '\n' ' ')"
mkdir -p $SG/shared; cp /tmp/fx_mila_key $SG/shared/k
OUT=$(env -u FARM_TEST_MODE MILA_SIGNING_KEY=/mnt/project-files/.mila-test-never HOME=$SG/home python3 -c "import sys;sys.path.insert(0,'$ROOTF/farm-runner');import runner as r;print(r.key_in_shared_folder('/mnt/project-files/.mila/mila-signing-key'), r.key_in_shared_folder('$SG/home/.mila/k'))"); expect "MILA a key in the shared project files is never used" "^True False$" "$OUT"
OUT=$(env -u MILA_SIGNING_KEY -u FARM_TEST_MODE HOME=$SG/home python3 "$ROOTF/farm-runner/runner.py" mila-keygen 2>&1); expect "MILA her own session makes her key, prints only the public key" "stays only in this session.*Public key for farm-rules.json" "$(echo "$OUT"|tr '\n' ' ')"
[ -f $SG/home/.mila/mila-signing-key ] && [ "$(stat -c %a $SG/home/.mila/mila-signing-key)" = 600 ] && ok "MILA key file sits in her session's home, owner-only" "600" || bad "MILA key file" ""
python3 -c "import json,sys;k=json.load(open(sys.argv[1]))['mila_signing']['public_key'];assert len(bytes.fromhex(k))==32 and k!='94a3ade11b6979b27e533893ad4820d84fa42e7e74f960966a5fa2832631c62c'" "$ROOTF/farm-rules.json" && ok "MILA the old shared key is retired; the registered key is the Mila sign workflow's" "32-byte key, not the old one" || bad "MILA old key still registered" ""
# Outside test mode, a verdict signed by any key other than the registered one is refused.
SGK=$SG/otherkey; python3 -c "import os;open('$SGK','w').write(os.urandom(32).hex())"
SR=$($R create --mode "Get Ready With Me" | sed -n 's/^Run ID: //p'); SS=$HOME/workspace/farm-runs/$SR/steps/step6-script; mkdir -p $SS; echo x > $SS/script.md
MILA_SIGNING_KEY=$SGK $R mila-sign --run $SR --step 6 --verdict APPROVE --file $SS/script.md --session session_OTHERKEYtest01 --out $SG/vk.md >/dev/null
OUT=$(env -u FARM_TEST_MODE -u FARM_TEST_MILA_PUBKEY MILA_SIGNING_KEY=/nonexistent python3 "$ROOTF/farm-runner/runner.py" approve-script $SR --verdict-file $SG/vk.md --session session_OTHERKEYtest01 2>&1; echo "exit $?")
echo "$OUT" | grep -q "exit 0" && bad "MILA a verdict signed by another key is refused" "$(echo "$OUT"|tr '\n' ' '|cut -c1-200)" || ok "MILA a verdict signed by another key is refused against the registered key" "$(echo "$OUT"|grep -iE "refused|signature|not mila"|head -1|cut -c1-120)"
python3 - "$ROOTF" <<'PYX' && ok "AGENTS every agent has its own Routine prompt that hands in with its session and stops on BLOCKED" "routines.json" || bad "AGENTS prompts" ""
import json,sys,os
root=sys.argv[1]; d=json.load(open(f"{root}/farm-agents/routines.json"))
roles=[a["role"] for a in d["agents"]]
assert {"TikTok Scout","TikTok Shop Agent","Photo Match checker","Story Agent","Casting / Image Agent","Video Agent","Mila"} <= set(roles), roles
for a in d["agents"]+[d["dispatcher"]]:
    t=open(f"{root}/farm-agents/{a['prompt']}").read()
    assert "BLOCKED" in t and "get_session" in t, a["prompt"]
    if a in d["agents"]: assert "--session" in t and "fire_trigger" in t, a["prompt"]
assert d["dispatcher"]["enabled"] is False
PYX

# ---------- MILA SIGN WORKFLOW (Glam, Nov 25, Option 1): the key lives only in the repo
# secret MILA_SIGNING_SEED; the workflow signs with Mila's session id and places the verdict.
WF="$ROOTF/.github/workflows/mila-sign.yml"
python3 - "$WF" <<'PYW' && ok "MILAWF the workflow reads only the secret MILA_SIGNING_SEED, runs only when started by hand, never prints the seed" "mila-sign.yml" || bad "MILAWF static checks" ""
import sys,yaml,re
t=open(sys.argv[1]).read(); d=yaml.safe_load(t)
on=d.get(True) or d.get("on")
assert list(on)==["workflow_dispatch"], on
assert "secrets.MILA_SIGNING_SEED" in t
assert not re.search(r"echo[^\n]*SEED_PHRASE", t)
assert "session_*" in t and "BLOCKED" in t
PYW
mkdir -p /tmp/fx_wf/rt; ln -sfn "$ROOTF/farm-runner" /tmp/fx_wf/farm-runner
python3 - "$WF" <<'PYW'
import sys,yaml
d=yaml.safe_load(open(sys.argv[1]))
for st in d["jobs"]["mila"]["steps"]:
    if st.get("name","").startswith("Sign and place"): open("/tmp/fx_wf/sign.sh","w").write(st["run"])
    if st.get("name","").startswith("Make Mila's key"): open("/tmp/fx_wf/key.sh","w").write(st["run"])
PYW
OUT=$(cd /tmp/fx_wf && SEED_PHRASE="" RUNNER_TEMP=/tmp/fx_wf/rt bash -e key.sh 2>&1; echo "exit $?"); expect "MILAWF no secret set = BLOCKED, nothing signed" "BLOCKED: the repo secret MILA_SIGNING_SEED is not set.*exit 1" "$(echo "$OUT"|tr '\n' ' ')"
RW=$($R create --mode "Get Ready With Me" | sed -n 's/^Run ID: //p'); W=$HOME/workspace/farm-runs/$RW/steps
printf 'Findings: x\nStory: Your feet hurt all week and you deserve a soft landing.\n' > $W/step2-scout/scout.md
printf 'product: TEST Scalp Oil\nlisting: test\n' > $W/step3-pick/pick.md
$R attach-photo $RW /tmp/fx_p.png --by Indigo >/dev/null; $R record-match $RW --checker Mila --grabber Indigo --verdict MATCH >/dev/null
printf 'CTA: linked below for you\nLINE 1: "Your wash day deserves five quiet minutes."\nShe works the oil into her scalp with her fingertips, product off frame.\nLINE 2: "Tap the orange cart."\n' > $W/step6-script/script.md
wfsign(){ cp /tmp/fx_mila_key /tmp/fx_wf/rt/mila-key; (cd /tmp/fx_wf && RUNNER_TEMP=/tmp/fx_wf/rt MILA_SIGNING_KEY=/tmp/fx_wf/rt/mila-key FARM_HOME=$HOME RUN_ID=$RW STEP=6 VERDICT=APPROVE NOTES="clean script" SESSION="$1" bash -e sign.sh 2>&1; echo "exit $?"); }
OUT=$(wfsign ""); expect "MILAWF no session id = BLOCKED, nothing signed" "BLOCKED: Mila's own session id.*exit 1" "$(echo "$OUT"|tr '\n' ' ')"
[ ! -e /tmp/fx_wf/rt/mila-key ] && ok "MILAWF the key file is wiped even when it stops" "gone" || bad "MILAWF key wiped on stop" ""
OUT=$(wfsign session_WFTESTMila0001); expect "MILAWF the workflow signs with Mila's session and Step 6 clears → Casting" "next is Casting.*MILA VERDICT PLACED.*exit 0" "$(echo "$OUT"|tr '\n' ' ')"
[ ! -e /tmp/fx_wf/rt/mila-key ] && ok "MILAWF the key file is wiped after signing" "gone" || bad "MILAWF key wiped after signing" ""
OUT=$($R proof $RW); expect "MILAWF proof shows the workflow's verdict under Mila's own session" "Step 6 +Mila +session_WFTESTMila0001" "$OUT"

# ---------- MUSE PUSH STARTS A RUN (Glam, Nov 25): a new farm-requests/*.json pushed to main opens the run
printf '{"mode": "", "product": "TEST Scalp Oil", "account": "@glamorousgrammyglowup"}\n' > /tmp/fx/req-a.json
OUT=$($R start-request /tmp/fx/req-a.json 2>&1); RQ=$(echo "$OUT" | sed -n 's/^Run ID: //p'); expect "PUSHRUN a request file opens a run and the Scout's job" "Chain: job opened for TikTok Scout" "$OUT"
OUT=$(python3 -c "import json;c=json.load(open('$HOME/workspace/farm-runs/$RQ/config.json'));print(c['pick'],'|',c['request'],'|',c['created_by'])"); expect "PUSHRUN the run records the product and which request opened it" "^TEST Scalp Oil \| req-a.json \| Muse request req-a.json" "$OUT"
OUT=$($R start-request /tmp/fx/req-a.json 2>&1; echo "exit $?"); expect "PUSHRUN the same request never opens a second run" "already started $RQ.*exit 2" "$(echo "$OUT"|tr '\n' ' ')"
printf '{"product": "x", "post": true}\n' > /tmp/fx/req-b.json
OUT=$($R start-request /tmp/fx/req-b.json 2>&1; echo "exit $?"); expect "PUSHRUN unknown fields are refused" "unknown field.*post.*exit 2" "$(echo "$OUT"|tr '\n' ' ')"
python3 - "$ROOTF/.github/workflows/start-run.yml" <<'PYW' && ok "PUSHRUN the workflow starts on a push of farm-requests/*.json to main, and the button still works" "push + workflow_dispatch" || bad "PUSHRUN workflow triggers" ""
import sys,yaml
d=yaml.safe_load(open(sys.argv[1])); on=d[True]
assert on["push"]["branches"]==["main"] and on["push"]["paths"]==["farm-requests/*.json"], on
assert "workflow_dispatch" in on and set(on["workflow_dispatch"]["inputs"])=={"mode","product","account"}
PYW
# The workflow's own push step, run against a scratch repo with a stand-in runner: only NEW top-level request files open runs.
python3 - "$ROOTF/.github/workflows/start-run.yml" <<'PYW'
import sys,yaml
for st in yaml.safe_load(open(sys.argv[1]))["jobs"]["start-run"]["steps"]:
    if st.get("name","").startswith("Open a run for each new request"): open("/tmp/fx_push.sh","w").write(st["run"])
PYW
PR=$(mktemp -d /tmp/fx_pushrepo.XXXXXX); mkdir -p $PR/farm-runner $PR/farm-requests/old; cd $PR; git init -q; git config user.email t@t; git config user.name t
printf 'import sys\nprint("Opened for "+sys.argv[2])\nprint("Status published to the Live Run Board")\n' > farm-runner/runner.py
echo '{}' > farm-requests/a.json; git add -A; git commit -qm one; C1=$(git rev-parse HEAD)
OUT=$(BEFORE=0000000000000000000000000000000000000000 AFTER=$C1 FARM_HOME=$PR/h bash -e /tmp/fx_push.sh 2>&1); expect "PUSHRUN first push: the new request opens a run" "Opened for farm-requests/a.json" "$OUT"
echo '{"mode":"x"}' > farm-requests/a.json; echo '{}' > farm-requests/b.json; echo '{}' > farm-requests/old/c.json; git add -A; git commit -qm two; C2=$(git rev-parse HEAD)
OUT=$(BEFORE=$C1 AFTER=$C2 FARM_HOME=$PR/h bash -e /tmp/fx_push.sh 2>&1); expect "PUSHRUN next push: only the NEW file opens a run (edited and sub-folder files don't)" "^== Request farm-requests/b.json Opened for farm-requests/b.json Status published to the Live Run Board$" "$(echo "$OUT"|tr '\n' ' '|sed 's/ *$//')"
git rm -q farm-requests/b.json; git commit -qm three; C3=$(git rev-parse HEAD)
OUT=$(BEFORE=$C2 AFTER=$C3 FARM_HOME=$PR/h bash -e /tmp/fx_push.sh 2>&1); expect "PUSHRUN deleting a request file opens nothing" "No new request files" "$OUT"
cd "$ROOTF"

# ---------- REPORT BLOCKED (Glam, Nov 25: the scout hit the security wall and never told her)
OUT=$($R report-blocked $RQ --step 3 --by "TikTok Shop Agent" --reason "test" 2>&1; echo "exit $?"); expect "BLOCKEDREPORT only the open step can be reported" "isn't the open job.*exit 2" "$(echo "$OUT"|tr '\n' ' ')"
OUT=$($R report-blocked $RQ --step 2 --by "Story Agent" --reason "TikTok asked for a text code" 2>&1; echo "exit $?"); expect "BLOCKEDREPORT another agent can't report for the Scout" "belongs to TikTok Scout.*exit 2" "$(echo "$OUT"|tr '\n' ' ')"
OUT=$($R report-blocked $RQ --step 2 --by "TikTok Scout" --reason "TikTok Shop Streamer Desktop asked for a text code; only Glam can pass it" 2>&1); expect "BLOCKEDREPORT the Scout reports BLOCKED" "BLOCKED reported on the board" "$OUT"
OUT=$(python3 -c "import json;d=json.load(open('$FARM_STATUS_OUT'));r=[x for x in d['runs'] if x['run_id']=='$RQ'][0];print(r['state'],'|',r['headline'],'|',r['needs'])"); expect "BLOCKEDREPORT the board shows it at once, in the Scout's words" "^STOPPED \| BLOCKED at Step 2 — TikTok Scout reported BLOCKED: TikTok Shop Streamer Desktop asked for a text code" "$OUT"
OUT=$($R status $RQ | grep HEADLINE); expect "BLOCKEDREPORT status shows it too" "HEADLINE: BLOCKED at Step 2 — TikTok Scout reported BLOCKED" "$OUT"
printf 'Findings: x\nStory: Your scalp gets tight after a long week of braids.\n' > /tmp/fx/scoutq.md
$R submit $RQ --step 2 --by "TikTok Scout" --file /tmp/fx/scoutq.md >/dev/null
[ ! -e $HOME/workspace/farm-runs/$RQ/steps/step2-scout/BLOCKED.md ] && grep -q "BLOCKED report on Step 2 cleared (TikTok Scout handed in)" $HOME/workspace/farm-runs/$RQ/RUN-SHEET.md && ok "BLOCKEDREPORT the report clears when the Scout hands in (kept in the gate log)" "cleared" || bad "BLOCKEDREPORT clears on hand-in" ""
grep -q "report-blocked" $HOME/workspace/farm-runs/$RQ/steps/step3-pick/JOB.md && ok "BLOCKEDREPORT every JOB.md says how to report BLOCKED" "JOB.md" || bad "BLOCKEDREPORT JOB.md line" ""

# ---------- MUSE IDS (Glam, Nov 25: "This is Muse job"): Muse jobs hand in with their own job id
RM=$($R create --mode "Get Ready With Me" | sed -n 's/^Run ID: //p'); MS=$HOME/workspace/farm-runs/$RM/steps
OUT=$(env -u FARM_TEST_MODE $R submit $RM --step 2 --by "TikTok Scout" --file /tmp/fx/scoutq.md 2>&1; echo "exit $?"); expect "MUSEID a hand-in with no id is still refused" "REFUSED — every hand-in names the agent's own id.*muse_.*exit 2" "$(echo "$OUT"|tr '\n' ' ')"
OUT=$($R submit $RM --step 2 --by "TikTok Scout" --file /tmp/fx/scoutq.md --session "muse_x" 2>&1; echo "exit $?"); expect "MUSEID a malformed Muse id is refused" "REFUSED.*exit 2" "$(echo "$OUT"|tr '\n' ' ')"
OUT=$($R submit $RM --step 2 --by "TikTok Scout" --file /tmp/fx/scoutq.md --session muse_job-scout-7f3a 2>&1); expect "MUSEID the Muse Scout job hands in with its own job id" "Handed to TikTok Shop Agent \(Step 3\)" "$OUT"
printf 'product: TEST Scalp Oil\nlisting: test\n' > /tmp/fx/pickm.md
OUT=$($R submit $RM --step 3 --by "TikTok Shop Agent" --file /tmp/fx/pickm.md --session muse_job-scout-7f3a 2>&1; echo "exit $?"); expect "MUSEID one Muse job can't play two roles on a run" "already acted as TikTok Scout.*exit 2" "$(echo "$OUT"|tr '\n' ' ')"
OUT=$($R submit $RM --step 3 --by "TikTok Shop Agent" --file /tmp/fx/pickm.md --session muse_job-shop-11c2 2>&1); expect "MUSEID a second Muse job hands in as the Shop Agent" "Handed to" "$OUT"
OUT=$($R proof $RM); expect "MUSEID proof lists each step's Muse job id" "Step 2 +TikTok Scout +muse_job-scout-7f3a +\(Muse job\).*Step 3 +TikTok Shop Agent +muse_job-shop-11c2 +\(Muse job\).*OK — 2 different id" "$(echo "$OUT"|tr '\n' ' ')"
grep -q "muse_ followed by YOUR OWN Muse scheduled job's id" $MS/step4-photo/JOB.md && grep -q -- "--session <your id>" $MS/step4-photo/JOB.md && ok "MUSEID every agent JOB.md tells Muse exactly what id to pass" "JOB.md" || bad "MUSEID JOB.md id line" ""
OUT=$(python3 -c "import sys,argparse;sys.path.insert(0,'$ROOTF/farm-runner');import runner as r;from pathlib import Path;print(r.session_guard(Path('$HOME/workspace/farm-runs/$RM'),'Mila',6,argparse.Namespace(session='muse_job-mila-0001'),'MILA APPROVAL'))" 2>&1); expect "MUSEID a Muse id can never stand in for Mila" "REFUSED — Mila's verdicts carry her own Claude session.*None" "$(echo "$OUT"|tr '\n' ' ')"

# ---------- FARM BRAIN (Glam, Nov 25: "update the farm brain" so every run reads today's decisions)
python3 - "$ROOTF" <<'PYB' && ok "BRAIN today's 11 decisions are laws in farm-rules.json, on the right agents" "laws + agents" || bad "BRAIN rules" ""
import json,sys
r=sys.argv[1]; d=json.load(open(f"{r}/farm-rules.json"))
ids={l["id"] for l in d["laws"]}
need={"time-cap","scout-trends-only","saved-product-list","weekly-lineup","photos-ahead","shop-from-lineup","selling-points","stock-check","angle-log","scorecard","muse-agents"}
assert need<=ids, need-ids
A={a["step"]:a for a in d["agents"]}
assert all("time-cap" in a["laws"] for a in d["agents"])
assert "scout-trends-only" in A[2]["laws"] and "Do not page the showcase" in A[2]["job"]
assert {"shop-from-lineup","stock-check","weekly-lineup"}<=set(A[3]["laws"]) and "weekly-lineup.json" in A[3]["job"]
assert "photos-ahead" in A[4]["laws"] and "BLOCKED" in A[4]["job"]
assert {"selling-points","angle-log"}<=set(A[6]["laws"]) and "selling-points.md" in A[6]["job"] and "angle-log.json" in A[6]["job"]
for f in ["showcase-products.json","weekly-lineup.json","angle-log.json","scorecard.json"]: json.load(open(f"{r}/farm-data/{f}"))
assert "## Farm brain changelog" in open(f"{r}/README.md").read()
PYB
RB=$($R create --mode "Get Ready With Me" | sed -n 's/^Run ID: //p')
grep -q "Time cap: 5 minutes" $HOME/workspace/farm-runs/$RB/steps/step2-scout/JOB.md && grep -q "trends-only quick check" $HOME/workspace/farm-runs/$RB/steps/step2-scout/JOB.md && ok "BRAIN a new run's Scout JOB.md carries the 5-minute cap and trends-only rule" "JOB.md" || bad "BRAIN Scout JOB.md" ""

python3 - "$ROOTF" <<'PYS' && ok "BRAIN products-only-from-Streamer-Desktop is the first law, on every agent, at the top of every prompt" "first law" || bad "BRAIN streamer rule" ""
import json,sys,glob
r=sys.argv[1]; d=json.load(open(f"{r}/farm-rules.json"))
assert d["laws"][0]["id"]=="streamer-desktop-only"
assert all(a["laws"][0]=="streamer-desktop-only" for a in d["agents"])
for f in glob.glob(f"{r}/farm-agents/prompts/*.md"):
    assert "products only from TikTok Shop Streamer Desktop" in open(f).read().split("\n",4)[2], f
PYS
RS=$($R create --mode "Get Ready With Me" | sed -n 's/^Run ID: //p')
sed -n 1,6p $HOME/workspace/farm-runs/$RS/steps/step2-scout/JOB.md | grep -q "HARD RULE: Products only from TikTok Shop Streamer Desktop" && ok "BRAIN the Streamer Desktop rule sits at the top of a new run's JOB.md" "JOB.md" || bad "BRAIN streamer rule in JOB.md" ""

echo; echo "SUMMARY: $P passed, $F failed"
