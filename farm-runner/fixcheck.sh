#!/bin/bash
# Farm runner fix-round test (Nov 24-25). Runs in a scratch HOME (/tmp/fx), never your real run folders.
# fixcheck.sh — reruns every failing audit case (#1-#6, #13, #21, #24-#29, #32)
# and the VERIFICATION regression cases (a)-(n) against the fixed runner.
export HOME=/tmp/fx; rm -rf $HOME; mkdir -p $HOME
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
K=$D/step8-package/package.md
lint(){ printf "%b" "$2" > $K; OUT=$($R lint $RUN 2>&1); expect "$1" "$3" "$OUT"; }
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
printf 'References: approved styled image + the real listing photo\nC01 - 8 seconds, she smiles at the counter, product stationary.\n' > $K
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
echo; echo "SUMMARY: $P passed, $F failed"
