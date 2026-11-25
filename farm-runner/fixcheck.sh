#!/bin/bash
# Farm runner fix-round test (Nov 24-25). Runs in a scratch HOME (/tmp/fx), never your real run folders.
# fixcheck.sh — reruns every failing audit case (#1-#6, #13, #21, #24-#29, #32)
# and the VERIFICATION regression cases (a)-(n) against the fixed runner.
export HOME=/tmp/fx; rm -rf $HOME; mkdir -p $HOME
# Live status goes to a scratch file during tests, never into the repo.
export FARM_STATUS_OUT=/tmp/fx/farm-status.json
R="python3 $(cd "$(dirname "$0")" && pwd)/runner.py"
P=0; F=0
ok(){ P=$((P+1)); echo "PASS  $1 :: $2"; }
bad(){ F=$((F+1)); echo "FAIL  $1 :: $2"; }
# expect <label> <grep-pattern> <text>
expect(){ if echo "$3" | grep -qE -- "$2"; then ok "$1" "$(echo "$3" | grep -E -- "$2" | head -1 | sed 's/  */ /g' | cut -c1-150)"; else bad "$1" "$(echo "$3" | head -3 | tr '\n' ' ' | cut -c1-200)"; fi; }
python3 -c "open('/tmp/fx_p.png','wb').write(b'\x89PNG\r\n\x1a\n')"

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
OUT=$($R approve-script $RUN; echo "exit $?"); expect "(j) approve refused on failing script" "APPROVAL REFUSED" "$OUT"
# ---------- #3 approval tied to script
printf 'CTA: it is linked below for you\nLINE 1: "Your feet hurt after every long shift."\nLINE 2: "Tap the orange cart."\n' > $S
OUT=$($R drive $RUN); expect "(g) drive stops at Glam's approval" "human gate: Glam's script approval" "$OUT"
$R approve-script $RUN >/dev/null
OUT=$($R status $RUN); expect "#3 approved script clears" "Step 6 +Script +CLEARED" "$OUT"
printf 'CTA: linked below\nLINE 1: "Your mornings are chaos and you need a win."\nLINE 2: "Tap the orange cart."\n' > $S
OUT=$($R status $RUN); expect "#3 edited script loses approval" "Step 6 +Script +WAITING +script changed after Glam's approval" "$OUT"
OUT=$($R drive $RUN); expect "#3 drive asks Glam again" "changed after Glam's approval" "$OUT"
$R approve-script $RUN >/dev/null
# ---------- Step 7/8 lint
cp /tmp/fx_p.png $D/step7-styled/model.png
$R approve-image $RUN >/dev/null  # chain: Glam approves the model photo (Step 7 gate)
K=$D/step8-package/package.md
CAP='Caption: Cloud Slides linked below for your tired feet\n#cloudslides #slides #comfyslides\n'
lint(){ printf "%b" "$2$CAP" > $K; OUT=$($R lint $RUN 2>&1); expect "$1" "$3" "$OUT"; }
lint "#4 jar/tube/'product in her hand' fails" 'References: approved styled image + the real listing photo\nClip 2: she picks up the jar and lifts it to camera.\nClip 3: she holds the tube up next to her face.\nClip 4: product in her hand, spraying.\n' "LINT RESULT: FAIL"
OUT2=$(echo "$OUT" | grep -c "\[STAGING\]"); [ "$OUT2" -ge 3 ] && ok "#4 three handling lines caught" "STAGING findings: $OUT2" || bad "#4 three handling lines caught" "STAGING findings: $OUT2"
lint "#4 stationary jar passes" 'References: approved styled image + the real listing photo\nC01 - 8 seconds. She smiles at the counter, the jar sits on the counter untouched.\n' "package passes"
lint "#28 five 10-second clips fail" 'References: styled image + listing photo\nClip 1 (10 seconds): "one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen"\nClip 2 (10 seconds)\nClip 3 (10 seconds)\nClip 4 (10 seconds)\nClip 5 (10 seconds)\n' "LINT RESULT: FAIL"
echo "$OUT" | grep -q "max 12 spoken words" && ok "#28 >12 words in a clip caught" "$(echo "$OUT"|grep -m1 'max 12')" || bad "#28 >12 words" "$OUT"
echo "$OUT" | grep -q "8 seconds flat" && ok "#28 10-second clip caught" "$(echo "$OUT"|grep -m1 '8 seconds flat'|cut -c1-120)" || bad "#28 10-second clip" ""
echo "$OUT" | grep -q "5 clips declared" && ok "#28 five clips caught" "$(echo "$OUT"|grep -m1 'clips declared'|cut -c1-120)" || bad "#28 five clips" ""
lint "#28 four 8s clips + 2s close-up pass" 'References: approved styled image + the real listing photo\nC01 - 8 seconds, she smiles at the counter.\nC02 - 8 seconds.\nC03 - 8 seconds.\nC04 - 8 seconds.\nC05 - close-up, 2 seconds of the real listing photo.\n' "package passes"
lint "(d) Nov 24 failure recipe fails" 'References: styled image\nnever spoken, never mouthed\nBOTTLE: the exact product: a tall rectangular clear bottle, the label reads Amococo, TURMERIC, 200ml\nShe tips the bottle over her open palm and golden oil pools in it; she holds the bottle.\n' "LINT RESULT: FAIL"
for c in "RETIRED GUARD TEXT" "LABEL WORDING" "PRODUCT DESCRIPTION" "STAGING" "REFERENCES"; do echo "$OUT" | grep -q "\[$c\]" && ok "(d) catches $c" "$(echo "$OUT"|grep -m1 "\[$c\]"|cut -c1-110)" || bad "(d) catches $c" ""; done
touch $D/step8-package/staging-proof.md
lint "(n-a) pour + proof still fails" 'References: approved styled image + the real listing photo\nShe pours the oil.\n' "LINT RESULT: FAIL"
lint "(n-b) texture shot + proof passes" 'References: approved styled image + the real listing photo\nTexture shot: the product on skin only, the bottle stays on the counter.\n' "package passes"
lint "(n-e) texture without counter fails" 'References: approved styled image + the real listing photo\nTexture shot: the product on skin only.\n' "LINT RESULT: FAIL"
lint "(n-d) two show-it shots fail" 'References: approved styled image + the real listing photo\nTexture shot: the product on skin only, the bottle stays on the counter.\nShow-it shot: fabric moving as she walks.\n' "LINT RESULT: FAIL"
lint "(n-f) dress fabric moving + proof passes" 'References: approved styled image + the real listing photo\nShow-it shot: fabric moving as she turns.\n' "package passes"
lint "(n-g) shoes walking + proof passes" 'References: approved styled image + the real listing photo\nShow-it shot: shoes on feet walking down the sidewalk.\n' "package passes"
lint "(n-j) show-it with no action fails" 'References: approved styled image + the real listing photo\nShow-it shot: the dress.\n' "LINT RESULT: FAIL"
lint "#4 show-it gadget 'spray in use' not double-flagged" 'References: approved styled image + the real listing photo\nShow-it shot: the mister in use, spraying a fine mist.\n' "package passes"
rm $D/step8-package/staging-proof.md
lint "(n-c/h) show-it without proof fails" 'References: approved styled image + the real listing photo\nShow-it shot: the gadget in use.\n' "LINT RESULT: FAIL"
printf "%b" 'References: approved styled image + the real listing photo\nC01 - 8 seconds, she smiles at the counter, product stationary.\n'"$CAP" > $K
OUT=$($R check $RUN --to 9; echo "exit $?"); expect "(d) clean package clears to 9" "CHECK to Step 9: OK" "$OUT"
# ---------- builds, handoff, verdicts (#1, #2, (f))
echo fake1 > $D/step9-builds/v1.mp4
OUT=$($R drive $RUN); expect "(f) auto-handoff then stop at Mila" "STOP at Step 10 — human gate: Mila" "$OUT"
H=$HOME/workspace/farm-qc-handoff/$RUN
OUT=$($R review-decision $RUN --decision approved; echo "exit $?"); expect "(f) review decision refused before PASS" "REVIEW DECISION REFUSED" "$OUT"
printf 'verdict: FAIL\nchecker: Mila\n' > $H/verdict.md
OUT=$($R drive $RUN); N=$(echo "$OUT" | grep -c "Collected Mila's verdict")
[ "$N" = 1 ] && ok "#2 FAIL collected exactly once" "Collected lines: $N" || bad "#2 FAIL collected once" "Collected lines: $N"
N=$(grep -c "Auto-collected" $HOME/workspace/farm-runs/$RUN/RUN-SHEET.md); [ "$N" = 1 ] && ok "#2 run sheet logs one collection" "Auto-collected lines: $N" || bad "#2 run sheet logs" "$N"
ls $H | grep -q "^verdict-collected-" && [ ! -e $H/verdict.md ] && ok "#1 verdict.md moved after collection" "$(ls $H | grep verdict)" || bad "#1 verdict moved" "$(ls $H)"
OUT=$($R drive $RUN); N=$(echo "$OUT" | grep -c "Collected"); [ "$N" = 0 ] && ok "#2 second drive re-collects nothing" "$(echo "$OUT"|tail -1|cut -c1-120)" || bad "#2 second drive" "$N"
OUT=$($R status $RUN); expect "#1 FAIL stops the run" "Step 10 .*INVALID.*FAIL" "$OUT"
echo fake2 > $D/step9-builds/v2.mp4
OUT=$($R status $RUN); expect "#1 new build after FAIL waits for Mila (old FAIL not reused)" "Step 10 .*WAITING +new build since Mila's verdict" "$OUT"
OUT=$($R drive $RUN); expect "#1 driver hands off the new build" "Auto-handoff" "$OUT"
[ -e $H/v2.mp4 ] && ok "#1 v2 in Mila's folder" "$(ls $H | tr '\n' ' ')" || bad "#1 v2 in folder" ""
printf 'verdict: PASS\nchecker: Mila\n' > $H/verdict.md
OUT=$($R drive $RUN); expect "(f) PASS collected, lands in Review" "Run is complete through Step 10" "$OUT"
OUT=$($R status $RUN); expect "(e) headline Ready for Glam — freeze on" "HEADLINE: Ready for Glam — freeze on." "$OUT"
echo fake3 > $D/step9-builds/v3.mp4
OUT=$($R status $RUN); expect "#1 build added after PASS is NOT covered" "Step 10 .*WAITING +new build since Mila's verdict" "$OUT"
expect "#1 headline no longer Ready for Glam" "HEADLINE: BLOCKED at Step 10" "$OUT"
OUT=$($R review-manifest); expect "#1 review shows not ready" "Not ready — waiting on Mila's check" "$OUT"
OUT=$($R drive $RUN); [ -e $H/v3.mp4 ] && ok "#1 v3 handed to Mila" "$(echo "$OUT"|grep -m1 Auto-handoff)" || bad "#1 v3 handed" "$OUT"
printf 'verdict: PASS\nchecker: Mila\n' > $H/verdict.md
echo changed > $D/step9-builds/v1.mp4
OUT=$($R drive $RUN); OUT=$($R status $RUN); expect "#1 verdict written before a build changed does not cover the new version" "Step 10 .*WAITING +new build since Mila's verdict" "$OUT"
printf 'verdict: PASS\nchecker: Mila\n' > $H/verdict.md; $R drive $RUN >/dev/null
OUT=$($R status $RUN); expect "#1 PASS on the exact current builds clears" "Step 10 .*CLEARED" "$OUT"
echo fake4 > $D/step9-builds/v4.mp4; $R drive $RUN >/dev/null; printf 'verdict: PASS\nchecker: Mila Rice\n' > $H/verdict.md; $R drive $RUN >/dev/null
OUT=$($R status $RUN); expect "(f) PASS signed by someone else refused" "Step 10 .*INVALID.*signed by 'Mila Rice'" "$OUT"
rm $D/step9-builds/v4.mp4; rm -f $H/v4.mp4; printf 'verdict: PASS\nchecker: Mila\n' > $H/verdict.md; $R drive $RUN >/dev/null
# ---------- #29 watch links
printf 'v1.mp4: https://drive.google.com/file/d/TESTID/view\n' > $D/step9-builds/links.md
$R review-manifest >/dev/null
grep -q '▶ Watch' $HOME/workspace/farm-runner/review-section.html && ok "#29 Watch link on card" "$(grep -o '<a href="[^"]*"' $HOME/workspace/farm-runner/review-section.html | head -1)" || bad "#29 watch link" ""
grep -q 'No watch link yet' $HOME/workspace/farm-runner/review-section.html && ok "#29 missing link says so" "No watch link yet — add it to links.md" || bad "#29 missing link msg" ""
grep -q '"watch_links"' $HOME/workspace/farm-runner/review-manifest.json && ok "#29 links in manifest JSON" "$(grep -m1 'drive.google' $HOME/workspace/farm-runner/review-manifest.json | sed 's/^ *//')" || bad "#29 json" ""
OUT=$($R handoff $RUN); echo "$OUT" | grep -q "links.md" && bad "#29 links.md not handed as a build" "$OUT" || ok "#29 links.md not handed as a build" "$(echo "$OUT"|head -1)"
OUT=$($R review-decision $RUN --decision approved; echo "exit $?"); expect "(f) review decision works after PASS (never posts)" "does not post" "$OUT"
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
OUT=$(FARM_RULES=$TMPR/ten.json $R approve-script $RUN); expect "RULES cap edited to 10 in the JSON -> same 11-word line fails, message says 10" "LINE 1 is 11 spoken words \(bar: 10 max\)" "$OUT"
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
$R approve-script $RUN >/dev/null  # the RULES tests edited the script; re-record Glam's approval
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
    for st in r["steps"]: assert set(st)=={"n","name","state","reason"}
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
OUT=$($R approve-script $RUN3 2>&1)
expect "INDIGO script: approval refused" "APPROVAL REFUSED" "$OUT"
expect "INDIGO 'right here on my vanity' caught as a use/ownership claim" "\[use-claim\] LINE 2" "$OUT"
expect "INDIGO held bottle + drop on her hand caught as staging" "\[staging\] script line 3" "$OUT"
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
OUT=$($R approve-script $RUN3 2>&1)
expect "rewritten script takes Glam's approval" "Recorded Glam's script approval" "$OUT"
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
grep -q "SENT BACK" $CS/step6-script/JOB.md && grep -q "stages the product" $CS/step6-script/JOB.md && ok "CHAIN findings written at the top of the Story Agent's JOB.md" "$(sed -n 3p $CS/step6-script/JOB.md | cut -c1-100)" || bad "CHAIN sent-back JOB.md" ""
OUT=$(python3 -c "import json;d=json.load(open('$FARM_STATUS_OUT'));r=[x for x in d['runs'] if x['run_id']=='$RC'][0];print(r['state'],'|',r['open_job']['agent'],'|',len(r['open_job']['sent_back']))"); expect "CHAIN status shows STOPPED, sent back to Story Agent" "^STOPPED \| Story Agent \| [1-9]" "$OUT"
printf 'CTA: it is linked below for you\nLINE 1: "Your feet hurt after every long shift."\nThe slides sit on the counter, no hands on them.\nLINE 2: "Tap the orange cart."\n' > $CH/script.md
OUT=$($R submit $RC --step 6 --by "Story Agent" --file $CH/script.md); expect "CHAIN corrected script passes → waiting on Glam" "Handed to Glam \(Step 6\)" "$OUT"
OUT=$(python3 -c "import json;d=json.load(open('$FARM_STATUS_OUT'));r=[x for x in d['runs'] if x['run_id']=='$RC'][0];print(r['open_job'],'|',r['owner'],'|',r['needs'])"); expect "CHAIN Glam gate: open_job null, owner Glam" "^None \| Glam \| Glam — approve the exact script" "$OUT"
OUT=$($R approve-script $RC); expect "CHAIN Glam's script approval → Casting / Image Agent" "next is Casting / Image Agent \(Step 7\)" "$OUT"
cp /tmp/fx_p.png $CH/model-uploaded.png
OUT=$($R submit $RC --step 7 --by "Casting / Image Agent" --file $CH/model-uploaded.png); expect "CHAIN model photo → waiting on Glam" "Handed to Glam \(Step 7\)" "$OUT"
OUT=$($R approve-image $RC); expect "CHAIN Glam's image approval → package job" "next is Story Agent \+ Video Agent \(Step 8\)" "$OUT"
printf 'References: approved model photo + the real listing photo\nC01 - 8 seconds, she smiles at the counter, product stationary.\n' > $CH/package-nocap.md
OUT=$($R submit $RC --step 8 --by "Story Agent" --file $CH/package-nocap.md; echo "exit $?"); expect "CHAIN package without a caption SENT BACK" "SENT BACK to Story Agent \+ Video Agent" "$OUT"
printf 'References: approved model photo + the real listing photo\nC01 - 8 seconds, she smiles at the counter, product stationary.\nCaption: Cloud Slides linked below for your tired feet\n#cloudslides #slides #comfyslides\n' > $CH/package.md
OUT=$($R submit $RC --step 8 --by "Video Agent" --file $CH/package.md); expect "CHAIN package with caption passes → Video Agent" "Handed to Video Agent \(Step 9\)" "$OUT"
echo "TEST build 1" > $CH/build-1.mp4
OUT=$($R submit $RC --step 9 --by "Indigo" --file $CH/build-1.mp4); expect "CHAIN build → Mila" "Handed to Mila \(Step 10\)" "$OUT"
[ -f $HOME/workspace/farm-qc-handoff/$RC/build-1.mp4 ] && [ -f $CS/step10-qc/JOB.md ] && ok "CHAIN build handed to Mila's QC folder + her JOB.md" "farm-qc-handoff/$RC/build-1.mp4" || bad "CHAIN Mila handoff" ""
OUT=$(python3 -c "import json;d=json.load(open('$FARM_STATUS_OUT'));r=[x for x in d['runs'] if x['run_id']=='$RC'][0];print(r['open_job']['agent'],'|',r['owner'])"); expect "CHAIN status open_job = Mila" "^Mila \| Mila" "$OUT"
printf 'verdict: PASS\nchecker: Mila\nscore: TEST — minors 4/4/5\n' > $CH/verdict.md
OUT=$($R submit $RC --step 10 --by "Mila" --file $CH/verdict.md); expect "CHAIN Mila's PASS → Glam's final review" "Handed to Glam: final review" "$OUT"
OUT=$($R status $RC); expect "CHAIN ends at Ready for Glam — freeze on" "HEADLINE: Ready for Glam — freeze on\." "$OUT"
OUT=$($R post $RC 2>&1; echo "exit $?"); expect "CHAIN there is no post command (nothing posts)" "invalid choice.*exit 2|exit 2" "$(echo "$OUT"|tr '\n' ' ')"
python3 - $C/handoffs.jsonl <<'PY' && ok "CHAIN handoffs.jsonl has every hop in order, with inputs + sha256" "hops ok" || bad "CHAIN handoffs order" "see above"
import json,sys
H=[json.loads(l) for l in open(sys.argv[1])]
want=[("Start a Run","TikTok Scout","handed off"),("TikTok Scout","TikTok Shop Agent","handed off"),
("TikTok Shop Agent","TikTok Shop Agent","handed off"),("TikTok Shop Agent","Photo Match checker","handed off"),
("Mila","Story Agent","handed off"),("Story Agent","Story Agent","sent back"),("Story Agent","Glam","waiting on Glam"),
("Glam","Casting / Image Agent","handed off"),("Casting / Image Agent","Glam","waiting on Glam"),
("Glam","Story Agent + Video Agent","handed off"),("Story Agent","Story Agent + Video Agent","sent back"),
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
rm -rf $CH
echo; echo "CHAIN HOPS (test data):"; cat /tmp/fx_hops.txt
echo; echo "SUMMARY: $P passed, $F failed"
