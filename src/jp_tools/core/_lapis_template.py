# Lapis Anki note template and CSS.
# Fill in the actual HTML/CSS here; anki_creator.py imports these constants.

RECOGNITION_QFMT: str = r"""
<!---------- Header ------------->
<header style="visibility: hidden"></header>

<main>
    <!--------- Vocab card ---------->
    {{^IsSentenceCard}} {{^IsWordAndSentenceCard}} {{^IsClickCard}}
    <div lang="ja" class="front-vocab">{{furigana:ExpressionFurigana}}</div>
    {{/IsClickCard}} {{/IsWordAndSentenceCard}} {{/IsSentenceCard}}

    <!------- Sentence card --------->
    {{#IsSentenceCard}}
    <div lang="ja" class="front-sentence">
        {{#SentenceFurigana}} {{kanji:SentenceFurigana}} {{/SentenceFurigana}}
        {{^SentenceFurigana}} {{kanji:Sentence}} {{/SentenceFurigana}}
    </div>
    {{/IsSentenceCard}}

    <!--------- Hint card ----------->
    {{#IsWordAndSentenceCard}}
    <div lang="ja" class="front-vocab">{{Expression}}</div>
    <div id="hint">
        {{#SentenceFurigana}} {{kanji:SentenceFurigana}} {{/SentenceFurigana}}
        {{^SentenceFurigana}} {{kanji:Sentence}} {{/SentenceFurigana}}
    </div>
    {{/IsWordAndSentenceCard}}

    <!-------- Click card ----------->
    {{#IsClickCard}}
    <div id="click">
        <div lang="ja" class="front-vocab">{{furigana:ExpressionFurigana}}</div>
    </div>
    {{/IsClickCard}}

    <!-- Hint -->
    {{#Hint}}
    <div id="hint">{{Hint}}</div>
    {{/Hint}}

</main>

<script>
    function ClickCard() {
        const clickElement = document.getElementById('click');

        // Store original content so that we can click back to it
        const originalContent = clickElement.innerHTML;

        // This is what it is going to click to
        const clickedContent = `
            <div lang="ja" class="front-sentence">
            {{#SentenceFurigana}} {{kanji:SentenceFurigana}} {{/SentenceFurigana}}
            {{^SentenceFurigana}} {{kanji:Sentence}} {{/SentenceFurigana}}
            </div>
        `;

        function toggleContent() {
            if (clickElement.innerHTML === originalContent) {
                clickElement.innerHTML = clickedContent;
            } else {
                clickElement.innerHTML = originalContent;
            }
        }
        // Implement the clicking mechanism
        clickElement.addEventListener('click', (e) => toggleContent());
        document.addEventListener('keydown', (e) => {
            if (event.key === 'c' | event.key === 'C') toggleContent();
        });
    }

    function initialize() {
        // Check what card type it is
        if (`{{IsClickCard}}`) ClickCard();
    }

    initialize();
</script>
<script>
/* AJT Japanese JS 24.10.8.1 */
/* DO NOT EDIT! This code will be overwritten by AJT Japanese. */
function ajt__kana_to_moras(text) { return text.match(/.[°゚]?[ァィゥェォャュョぁぃぅぇぉゃゅょ]?/gu); } function ajt__norm_handakuten(text) { return text.replace(/\u{b0}/gu, "\u{309a}"); } function ajt__make_pattern(kana, pitch_type, pitch_num) { const moras = ajt__kana_to_moras(ajt__norm_handakuten(kana)); switch (pitch_type) { case "atamadaka": return ( `<span class="ajt__HL">${moras[0]}</span>` + `<span class="ajt__L">${moras.slice(1).join("")}</span>` + `<span class="ajt__pitch_number_tag">1</span>` ); break; case "heiban": return ( `<span class="ajt__LH">${moras[0]}</span>` + `<span class="ajt__H">${moras.slice(1).join("")}</span>` + `<span class="ajt__pitch_number_tag">0</span>` ); break; case "odaka": return ( `<span class="ajt__LH">${moras[0]}</span>` + `<span class="ajt__HL">${moras.slice(1).join("")}</span>` + `<span class="ajt__pitch_number_tag">${moras.length}</span>` ); break; case "nakadaka": return ( `<span class="ajt__LH">${moras[0]}</span>` + `<span class="ajt__HL">${moras.slice(1, Number(pitch_num)).join("")}</span>` + `<span class="ajt__L">${moras.slice(Number(pitch_num)).join("")}</span>` + `<span class="ajt__pitch_number_tag">${pitch_num}</span>` ); break; } } function ajt__format_new_ruby(kanji, readings) { if (readings.length > 1) { return `<ruby>${ajt__format_new_ruby(kanji, readings.slice(0, -1))}</ruby><rt>${readings.slice(-1)}</rt>`; } else { return `${kanji}<rt>${readings.join("")}</rt>`; } } function ajt__zip(array1, array2) { let zipped = []; const size = Math.min(array1.length, array2.length); for (let i = 0; i < size; i++) { zipped.push([array1[i], array2[i]]); } return zipped; } function ajt__make_accent_list_item(kana_reading, pitch_accent) { const list_item = document.createElement("li"); for (const [reading_part, pitch_part] of ajt__zip(kana_reading.split("・"), pitch_accent.split(","))) { const [pitch_type, pitch_num] = pitch_part.split("-"); const pattern = ajt__make_pattern(reading_part, pitch_type, pitch_num); list_item.insertAdjacentHTML("beforeend", `<span class="ajt__downstep_${pitch_type}">${pattern}</span>`); } return list_item; } function ajt__make_accents_list(ajt_span) { const accents = document.createElement("ul"); for (const accent_group of ajt_span.getAttribute("pitch").split(" ")) { accents.appendChild(ajt__make_accent_list_item(...accent_group.split(":"))); } return accents; } function ajt__make_popup_div(content) { const frame_top = document.createElement("div"); frame_top.classList.add("ajt__frame_title"); frame_top.innerText = "Information"; const frame_bottom = document.createElement("div"); frame_bottom.classList.add("ajt__frame_content"); frame_bottom.appendChild(content); const popup = document.createElement("div"); popup.classList.add("ajt__info_popup"); popup.appendChild(frame_top); popup.appendChild(frame_bottom); return popup; } function ajt__find_word_info_popup(word_span) { return word_span.querySelector(".ajt__info_popup"); } function ajt__find_popup_x_corners(popup_div) { const elem_rect = popup_div.getBoundingClientRect(); const right_corner_x = elem_rect.x + elem_rect.width; return { x_start: elem_rect.x, x_end: right_corner_x, shifted_x_start: elem_rect.x + elem_rect.width / 2, shifted_x_end: right_corner_x + elem_rect.width / 2, }; } function ajt__word_info_on_mouse_enter(word_span) { const popup_div = ajt__find_word_info_popup(word_span); if (popup_div) { ajt__word_info_on_mouse_leave(word_span); const x_pos = ajt__find_popup_x_corners(popup_div); if (x_pos.x_start < 0) { popup_div.classList.add("ajt__left-corner"); popup_div.style.setProperty("--shift-x", `${Math.ceil(-x_pos.x_start)}px`); } else if (x_pos.shifted_x_end < window.innerWidth) { popup_div.classList.add("ajt__in-middle"); } } } function ajt__word_info_on_mouse_leave(word_span) { const popup_div = ajt__find_word_info_popup(word_span); if (popup_div) { popup_div.classList.remove("ajt__left-corner", "ajt__in-middle"); } } function ajt__adjust_popup_position_on_mouse_enter(word_info_span) { word_info_span.addEventListener("mouseenter", (event) => ajt__word_info_on_mouse_enter(event.currentTarget)); word_info_span.addEventListener("mouseleave", (event) => ajt__word_info_on_mouse_leave(event.currentTarget)); } function ajt__format_readings_as_list(readings) { const readings_items = readings.map((reading) => `<li>${reading}</li>`).join(""); const list_elem = document.createElement("ol"); list_elem.classList.add("ajt__readings_list"); list_elem.insertAdjacentHTML("beforeend", readings_items); return list_elem; } function ajt__find_kanji_readings(ruby_tag) { const separators = /[\s;,.、・。]+/iu; const kanji = (ruby_tag.querySelector("rb") || ruby_tag.firstChild).textContent.trim(); const readings = ruby_tag .querySelector("rt") .textContent.split(separators) .map((str) => str.trim()) .filter((str) => str.length); return { kanji: kanji, readings: readings }; } function ajt__reformat_multi_furigana() { const max_inline = 2; document.querySelectorAll("ruby:not(ruby ruby):not(.ajt__furigana_list ruby)").forEach((ruby) => { try { const { kanji, readings } = ajt__find_kanji_readings(ruby); if (readings.length > 1) { ruby.innerHTML = ajt__format_new_ruby(kanji, readings.slice(0, max_inline)); } if (readings.length > max_inline && !ruby.matches(".ajt__word_info ruby")) { const content_ul = ajt__format_readings_as_list(readings); const popup = ajt__make_popup_div(content_ul); const wrapper = document.createElement("span"); ruby.replaceWith(wrapper); wrapper.appendChild(ruby); wrapper.appendChild(popup); wrapper.classList.add("ajt__furigana_list"); ajt__adjust_popup_position_on_mouse_enter(wrapper); } } catch (error) { console.error(error); } }); } function ajt__create_popups() { for (const [idx, span] of document.querySelectorAll(".ajt__word_info").entries()) { if (span.matches(".jpsentence .background *")) { continue; } if (ajt__find_word_info_popup(span)) { continue; } try { const content_ul = ajt__make_accents_list(span); const popup = ajt__make_popup_div(content_ul); popup.setAttribute("ajt__popup_idx", idx); span.setAttribute("ajt__popup_idx", idx); span.appendChild(popup); ajt__adjust_popup_position_on_mouse_enter(span); } catch (error) { console.error(error); } } } function ajt__main() { ajt__create_popups(); ajt__reformat_multi_furigana(); } if (document.readyState === "loading") { document.addEventListener("DOMContentLoaded", ajt__main); } else { ajt__main(); }
</script>
"""

RECOGNITION_AFMT: str = r"""
<!---------- Header ------------->
<header>
    <div class="top-container">
        <!-- Show the frequency number -->
        {{FreqSort}}

        <!-- The frequency list -->
        {{#Frequency}}
        <span class="freq-dropdown">
            <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" class="dropdown-arrow-svg"
                viewBox="0 0 16 16">
                <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"></path>
                <path d="M 12.7,6.5 H 3.3 L 8,11 Z"></path>
            </svg>
            <div class="freq-list-container">{{Frequency}}</div>
        </span>
        {{/Frequency}}
    </div>
</header>

<main lang="ja">
    <div class="template">

        <!-- The first row (vocab box+picture) -->
        <div class="def-header">
            <div class="dh-left">
                <div class="show-furigana vocab">
                    {{#ExpressionFurigana}}{{furigana:ExpressionFurigana}}{{/ExpressionFurigana}}
                    {{^ExpressionFurigana}}{{Expression}}{{/ExpressionFurigana}}
                </div>

                <!-- Reading + Pitch Accent -->
                <div class="info">
                    <div class="pitch">
                        {{#ExpressionFurigana}}{{kana:ExpressionFurigana}}{{/ExpressionFurigana}}
                        {{^ExpressionFurigana}}{{ExpressionReading}}{{/ExpressionFurigana}}
                    </div>

                    <!-- Pitch Accent -->
                    {{#PitchPosition}}
                    <span id="pitch-tags" class="tags"> {{PitchPosition}} </span>
                    {{/PitchPosition}}
                    <br />
                    <div class="audio-buttons">{{ExpressionAudio}} {{SentenceAudio}}</div>
                </div>
            </div>

            <!-- Image -->
            <div class="dh-right">
                {{#Picture}}
                <div class="image tappable {{Tags}}">{{Picture}}</div>
                {{/Picture}}
            </div>
        </div>

        <!-- Sentence-->
        <br>
        <div class="sentence">
            {{#SentenceFurigana}} {{furigana:SentenceFurigana}} {{/SentenceFurigana}}
            {{^SentenceFurigana}} {{furigana:Sentence}} {{/SentenceFurigana}}
        </div>

        <!-- Sentence Mobile -->
        <div class="sentence-mobile">
            {{#SentenceFurigana}} {{furigana:SentenceFurigana}} {{/SentenceFurigana}}
            {{^SentenceFurigana}} {{furigana:Sentence}} {{/SentenceFurigana}}
        </div>

        <!-- The entire definition blockquote -->
        <div class="def-info-container">
            <div class="def-info"></div>
        </div>
        <blockquote class="main-def def-blockquote">
            {{#DefinitionPicture}}
            <div class="def-image tappable">{{DefinitionPicture}}</div>
            {{/DefinitionPicture}}
            <div class="definition">
                {{#SelectionText}}
                <div id="selection" data-display-name="Text Selection">{{furigana:SelectionText}}</div>
                {{/SelectionText}}
                {{#MainDefinition}}
                <div id="primary" data-display-name="Primary Definition">{{furigana:MainDefinition}}</div>
                {{/MainDefinition}}
                <div id="glossaries" data-display-name="Glossaries">{{furigana:Glossary}}</div>
            </div>
        </blockquote>

        <!------- Image modal --------->
        <div class="modal-bg tappable">
            <div class="img-popup"></div>
        </div>

        {{#MiscInfo}}
        <div style="text-align: center">
            <div>
                <details>
                    <summary>Misc. info</summary>
                    <div class="misc-info popup">
                        === Details ===
                        <br />
                        {{MiscInfo}}
                    </div>
                </details>
            </div>
        </div>
        {{/MiscInfo}}
</main>

<!----------- Footer ------------->
<footer lang="ja">
    <br>
    <div class="bot-container">
        {{#Tags}}
        <div class="tags-container">
            <div class="tags">{{Tags}}</div>
        </div>
        {{/Tags}}
    </div>
</footer>

<!----------- Scripts ------------>
<script>
    // This code is concerned with calculating the Pitch Accent and constructing the pitch accent graphs
    function isOdaka(pitchNumber) {
        const kana = `{{kana:ExpressionFurigana}}` || `{{ExpressionReading}}`;
        return (
            kana !== null &&
            kana.replace(/[ァィゥェォャュョヮぁぃぅぇぉゃゅょゎ]/g, "").length === pitchNumber
        );
    }

    function getPitchCategories() {
        const validTypes = "(heiban|atamadaka|nakadaka|odaka|kifuku)";
        return [...`{{PitchCategories}}`.matchAll(validTypes)].map(m => m[0]);
    }

    function hasVerbOrAdjEnding() {
        const endings = ["い", "う", "く", "す", "つ", "ぶ", "む", "る"];
        return endings.some(ending => `{{Expression}}`.replace("</div>","").endsWith(ending));
    }

    function getPitchType(pitchPosition) {
        const pitchCategories = getPitchCategories();
        const kifukuTags = ["adj-i", "v1", "v2", "v4", "v5", "vs-", "vz", "vk", "vn", "vr"];
        let canBeKifuku = pitchCategories.includes("kifuku");
        canBeKifuku ||= kifukuTags.some(tag => `{{PitchCategories}}`.includes(tag));
        if (canBeKifuku || (pitchCategories.length == 0 && hasVerbOrAdjEnding())) {
            return pitchPosition === 0 ? "heiban" : "kifuku";
        }

        if (pitchPosition === 0) {
            return "heiban";
        } else if (pitchPosition === 1) {
            return "atamadaka";
        } else if (pitchPosition > 1) {
            return isOdaka(pitchPosition) ? "odaka" : "nakadaka";
        }
    }

    // Show the color
    function paintTargetWord() {
        const pitchPositions = `{{PitchPosition}}`.match(/^\d+|\d+\b|\d+(?=\w)/g);
        if (pitchPositions === null) return;

        const pitchType = getPitchType(Number(pitchPositions[0]));
        const sentences = Array.from(
            document.querySelectorAll(".sentence, .definition, .sentence-mobile"),
        );
        for (const sentence of sentences) {
            for (const targetWord of sentence.getElementsByTagName("b")) {
                targetWord.classList.add(pitchType);
            }
        }

        const vocabElement = document.querySelector(".vocab");
        if (vocabElement !== null) {
            vocabElement.classList.add(pitchType);
        }
    }

    // Seperate Tags by space, and show them in their own boxes
    function tweakHTML() {
        // Split tags
        const tagsContainer = document.querySelector(".tags-container");
        const tags = `{{Tags}}`.split(" ");
        if (tagsContainer) {
            tagsContainer.innerHTML = "";
            for (tag of tags) {
                const tagElem = document.createElement("div");
                tagElem.className = "tags";
                tagElem.innerText = tag;
                tagsContainer.appendChild(tagElem);
            }
        }
    }

    function groupMoras(kana) {
        let currentChar = "";
        let nextChar = "";
        const groupedMoras = [];
        const check = ["ァ", "ィ", "ゥ", "ェ", "ォ", "ャ", "ュ", "ョ", "ヮ", "ぁ", "ぃ", "ぅ", "ぇ", "ぉ", "ゃ", "ゅ", "ょ", "ゎ"];

        for (let i = 0; i < kana.length; i++) {
            currentChar = kana[i];
            nextChar = i < kana.length - 1 && kana[i + 1];
            if (check.includes(nextChar)) {
                groupedMoras.push(currentChar + nextChar);
                i += 1;
            } else {
                groupedMoras.push(currentChar);
            }
        }
        return groupedMoras;
    }

    function getPitchPattern(pitchPosition) {
        // 0 = low
        // 1 = high
        // 2 = high to low

        const kana = `{{kana:ExpressionFurigana}}` || `{{ExpressionReading}}`;
        const moras = groupMoras(kana);
        let pattern = [];

        if (pitchPosition === 0) {
            // 平板
            pattern = [
                ...Array(moras[0].length).fill("0"),
                ...Array(kana.length - moras[0].length).fill("1"),
            ];
        } else if (pitchPosition === 1) {
            // 頭高
            pattern = [
                ...(moras[0].length === 2 ? ["1", "2"] : ["2"]),
                ...Array(kana.length - moras[0].length).fill("0"),
            ];
        } else if (pitchPosition > 1) {
            if (isOdaka(pitchPosition)) {
                // 尾高
                pattern = [
                    ...Array(moras[0].length).fill("0"),
                    ...Array(kana.length - moras[0].length - 1).fill("1"),
                    "2",
                ];
            } else {
                // 中高
                let afterDrop = false;
                for (let i = 0; i < moras.length; i++) {
                    if (i === 0) {
                        pattern = Array(moras[0].length).fill("0");
                    } else if (i + 1 === pitchPosition) {
                        pattern =
                            moras[i].length === 2
                                ? [...pattern, "1", "2"]
                                : [...pattern, "2"];
                        afterDrop = true;
                    } else if (afterDrop) {
                        pattern = [...pattern, ...Array(moras[i].length).fill("0")];
                    } else {
                        pattern = [...pattern, ...Array(moras[i].length).fill("1")];
                    }
                }
            }
        }
        return pattern;
    }

    function constructPitch() {
        const pitchPositions = `{{PitchPosition}}`.match(/^\d+|\d+\b|\d+(?=\w)/g);
        if (!pitchPositions) return;

        const kana = `{{kana:ExpressionFurigana}}` || `{{ExpressionReading}}`;
        const pitch = document.querySelector(".pitch");
        const pitchTags = document.querySelector("#pitch-tags");

        const createPitchSpan = (pitchClass, pitchChar) => {
            const pitchSpan = document.createElement("span");
            const charSpan = document.createElement("span");
            const lineSpan = document.createElement("span");

            pitchSpan.classList.add(pitchClass);
            charSpan.classList.add("pitch-char");
            charSpan.innerText = pitchChar;
            lineSpan.classList.add("pitch-line");

            pitchSpan.appendChild(charSpan);
            pitchSpan.appendChild(lineSpan);

            return pitchSpan;
        };

        pitch.innerHTML = "";
        pitchTags.innerHTML = "";
        pitchTags.style.display = "inline-block";
        let uniquePitchPositions = [...new Set(pitchPositions)];

        const pitchList = document.createElement("ul");
        const pitchTagList = document.createElement("ul");

        for (let pitchPosition of uniquePitchPositions) {
            const pitchTag = document.createElement("li");
            pitchTag.textContent = pitchPosition;

            const pattern = getPitchPattern(Number(pitchPosition));

            const pitchItem = document.createElement("li");
            pitchItem.classList.add("pitch-item");
            pitchItem.classList.add(getPitchType(Number(pitchPosition)));

            for (let i = 0; i < kana.length; i++) {
                if (pattern[i] === "0")
                    pitchItem.appendChild(createPitchSpan("pitch-low", kana[i]));
                else if (pattern[i] === "1")
                    pitchItem.appendChild(createPitchSpan("pitch-high", kana[i]));
                else if (pattern[i] === "2")
                    pitchItem.appendChild(createPitchSpan("pitch-to-drop", kana[i]));
                else
                    console.error(
                        "pattern[i] found undefined value. pattern is",
                        pattern,
                    );
            }
            pitchTagList.appendChild(pitchTag);
            pitchList.appendChild(pitchItem);
        }

        pitch.appendChild(pitchList);
        pitchTags.appendChild(pitchTagList);
    }

    // Returns the dictionary content, without the dictionary name.
    function getDictionaryContent(dictionarySelector) {
        const dictionary = document.querySelector(dictionarySelector);
        if (!dictionary) return null;
        const contentInSpan = dictionary.querySelector(":scope > span");
        if (contentInSpan) return contentInSpan;

        const hasDictName = dictionary.querySelector(":scope > i");
        if (!hasDictName) return dictionary;

        let dictionaryCopy = dictionary.cloneNode(true);
        dictName = dictionaryCopy.querySelector(":scope > i");
        dictName.remove();
        return dictionaryCopy;
    }

    function isPrimaryEqualToGloss() {
        const isJPMNConverted = document.querySelector(".definition li[data-details]");
        if (isJPMNConverted) return false;
        // single dict formatting
        const isSingleDict = document.querySelectorAll("#glossaries > div > ol").length === 0;
        if (isSingleDict) {
            const primaryDictName = document.querySelector("#primary > div > i");
            const glossariesDictName = document.querySelector("#glossaries > div > i");
            // Compare dicts names if present
            if (primaryDictName && glossariesDictName) {
                return primaryDictName.textContent === glossariesDictName.textContent;
            }
            // Compare content otherwise
            const primaryDict = getDictionaryContent("#primary > div");
            const glossariesDict = getDictionaryContent("#glossaries > div");
            if (!primaryDict || !glossariesDict ) return false;
            return primaryDict.innerHTML.trim() === glossariesDict.innerHTML.trim();
        }

        // multiple dicts
        const primaryDicts = document.querySelectorAll("#primary li[data-dictionary]");
        const glossariesDicts = document.querySelectorAll("#glossaries li[data-dictionary]");
        return primaryDicts.length === glossariesDicts.length
    }

    // Removes Unnecessary definitions
    function cleanUpDefinitions() {
        let selection = document.getElementById("selection");
        let primary = document.getElementById("primary");
        let glossaries = document.getElementById("glossaries");
        if (selection && selection.textContent === "") {
            selection.remove();
        }
        if (primary && primary.textContent === "") {
            primary.remove();
            primary = null;
        }
        if (glossaries && glossaries.textContent === "") {
            glossaries.remove();
            glossaries = null;
        }
        else if (primary && glossaries && isPrimaryEqualToGloss()) {
            glossaries.remove();
        }
    }

    // Display definition corresponding to index
    function updateDefDisplay() {
        const definitions = document.querySelectorAll(
            ".main-def > .definition > div"
        );

        let n_defs = definitions.length;
        if (n_defs === 1) definitions[0].classList.remove("hidden");
        if (n_defs <= 1) return;

        let currentIndex = document.head.getAttribute("data-def-index");
        currentIndex = currentIndex % n_defs;
        while (currentIndex < 0) currentIndex += n_defs;

        for (let idx = 0; idx < n_defs; idx++) {
            definitions[idx].classList.add("hidden");
        }
        definitions[currentIndex].classList.remove("hidden");

        const defDisplayName = definitions[currentIndex].getAttribute("data-display-name")
        const indexDisplay = document.querySelector(".def-info");
        indexDisplay.style.opacity = 1;
        indexDisplay.innerText = `${defDisplayName} ${currentIndex + 1}/${n_defs}`;
    }

    function setUpDefToggle() {
        document.head.setAttribute("data-def-index", 0);
        cleanUpDefinitions();

        // hide all but first definition
        let definitions = document.querySelectorAll(".main-def > .definition > div");
        Array.from(definitions).slice(1).forEach(def => { def.classList.add("hidden"); });
        // no need for toggling on less than 2 definitions
        if (definitions.length < 2) return;

        let mainDefContainer = document.querySelector(".main-def");
        const leftEdge = document.createElement("div");
        const rightEdge = document.createElement("div");
        leftEdge.classList.add("left-edge");
        leftEdge.classList.add("tappable");
        rightEdge.classList.add("right-edge");
        rightEdge.classList.add("tappable");
        mainDefContainer.appendChild(leftEdge);
        mainDefContainer.appendChild(rightEdge);

        const changeIndex = (value) => {
            // sync index between clicks and arrowkeys
            index = Number(document.head.getAttribute("data-def-index"));
            index += value;
            document.head.setAttribute("data-def-index", index);
            updateDefDisplay();
        };

        leftEdge.addEventListener("click", (e) => changeIndex(-1));
        rightEdge.addEventListener("click", (e) => changeIndex(1));

        // Add key listener only once per session
        if (document.head.classList.contains("has-listener")) return;
        document.addEventListener("keydown", (e) => {
            if (e.key === "ArrowLeft") changeIndex(-1);
            else if (e.key === "ArrowRight") changeIndex(1);
        });

        document.head.classList.add("has-listener");
    }

    // This just handles clicking and showing images
    function clickImages() {
        const modalBg = document.querySelector(".modal-bg");
        const imgPopup = document.querySelector(".img-popup");
        const images = Array.from(document.querySelectorAll(".image img, .def-image img"));

        if (images.length < 1) return;

        for (let image of images) {
            image.addEventListener("click", () => {
                const imgPopupContainer = document.createElement("div");
                const imgPopupImg = document.createElement("img");

                imgPopupContainer.classList.add("img-popup-container");
                imgPopupImg.src = image.src;
                imgPopupImg.classList.add("img-popup-img");

                if (image.height > image.width) {
                    imgPopupContainer.style.height = "calc(100% - 20px)";
                    imgPopupContainer.style.width = "max-content";
                }
                imgPopup.innerHTML = "";
                imgPopup.appendChild(imgPopupContainer);
                imgPopupContainer.appendChild(imgPopupImg);

                document.body.classList.add("img-popup");
                modalBg.style.display = "block";
                imgPopupContainer.style.display = "flex";
            });
        }

        modalBg.addEventListener("click", () => {
            document.body.classList.remove("img-popup");
            modalBg.style.display = "none";
            imgPopup.innerHTML = "";
        });
    }

    // Format plaintext frequencies into a list
    function formatFrequencyList() {
        const frequency = document.querySelector('.freq-list-container');
        if (!frequency) return;
        const frequencyList = frequency.querySelector('ul');
        // Already a list; nothing to do
        if (frequencyList) return;

        const freqs = frequency.innerText.split(',');
        const freqHtml = `<ul>${freqs.map(freq => `<li>${freq.trim()}</li>`).join('')}</ul>`
        frequency.innerHTML = freqHtml;
    }

    // Sets the height of dhLeft, dhRight, defHeader as a whole
    function setDHHeight() {
        var dhLeft = document.querySelector('.dh-left');
        var dhRight = document.querySelector('.dh-right .image img');
        var defHeader = document.querySelector('.def-header')

        if (dhLeft && dhRight) {
            var dhLeftHeight = dhLeft.offsetHeight;
            dhRight.style.maxHeight = `${dhLeftHeight}px`;
            defHeader.style.maxHeight = `${dhLeftHeight}px`;
        }
    }

    // Hides the dictionaries user selected in MainDefinition in Glossary field, if any
    function hideCorrectDefinition() {
        // Do nothing if css rule already exists
        if (document.querySelector("style#hide-main-def")) return;

        let primaryDicts = document.querySelectorAll("#primary li[data-dictionary]");
        if (primaryDicts.length === 0) return;

        let style = document.createElement('style');
        style.type = 'text/css';
        style.id = "hide-main-def";

        const cssSelector = Array.from(primaryDicts).map((dict) =>
            `#glossaries li[data-dictionary="${dict.getAttribute("data-dictionary")}"]`
        ).join(", ");
        const cssRules = `${cssSelector} { display:none !important; }`;
        style.appendChild(document.createTextNode(cssRules));

        let defContainer = document.querySelector("blockquote.main-def");
        defContainer.appendChild(style);
    }

    // Moves Primary Dicts into the same list
    function movePrimaryDicts() {
        let primaryDicts = document.querySelectorAll("#primary li[data-dictionary]");
        let firstList = document.querySelector("#primary .yomitan-glossary > ol:has( li[data-dictionary])");
        for (let idx = 1; idx < primaryDicts.length; idx++) {
            firstList.appendChild(primaryDicts[idx]);
        }
    }

    // Initialize all functions!!!
    function initialize() {
        tweakHTML();
        paintTargetWord();
        constructPitch();
        setUpDefToggle();
        clickImages();
        formatFrequencyList();
        setDHHeight();
        hideCorrectDefinition();
        movePrimaryDicts();
    }

    initialize();
</script>

<script>
/* AJT Japanese JS 24.10.8.1 */
/* DO NOT EDIT! This code will be overwritten by AJT Japanese. */
function ajt__kana_to_moras(text) { return text.match(/.[°゚]?[ァィゥェォャュョぁぃぅぇぉゃゅょ]?/gu); } function ajt__norm_handakuten(text) { return text.replace(/\u{b0}/gu, "\u{309a}"); } function ajt__make_pattern(kana, pitch_type, pitch_num) { const moras = ajt__kana_to_moras(ajt__norm_handakuten(kana)); switch (pitch_type) { case "atamadaka": return ( `<span class="ajt__HL">${moras[0]}</span>` + `<span class="ajt__L">${moras.slice(1).join("")}</span>` + `<span class="ajt__pitch_number_tag">1</span>` ); break; case "heiban": return ( `<span class="ajt__LH">${moras[0]}</span>` + `<span class="ajt__H">${moras.slice(1).join("")}</span>` + `<span class="ajt__pitch_number_tag">0</span>` ); break; case "odaka": return ( `<span class="ajt__LH">${moras[0]}</span>` + `<span class="ajt__HL">${moras.slice(1).join("")}</span>` + `<span class="ajt__pitch_number_tag">${moras.length}</span>` ); break; case "nakadaka": return ( `<span class="ajt__LH">${moras[0]}</span>` + `<span class="ajt__HL">${moras.slice(1, Number(pitch_num)).join("")}</span>` + `<span class="ajt__L">${moras.slice(Number(pitch_num)).join("")}</span>` + `<span class="ajt__pitch_number_tag">${pitch_num}</span>` ); break; } } function ajt__format_new_ruby(kanji, readings) { if (readings.length > 1) { return `<ruby>${ajt__format_new_ruby(kanji, readings.slice(0, -1))}</ruby><rt>${readings.slice(-1)}</rt>`; } else { return `${kanji}<rt>${readings.join("")}</rt>`; } } function ajt__zip(array1, array2) { let zipped = []; const size = Math.min(array1.length, array2.length); for (let i = 0; i < size; i++) { zipped.push([array1[i], array2[i]]); } return zipped; } function ajt__make_accent_list_item(kana_reading, pitch_accent) { const list_item = document.createElement("li"); for (const [reading_part, pitch_part] of ajt__zip(kana_reading.split("・"), pitch_accent.split(","))) { const [pitch_type, pitch_num] = pitch_part.split("-"); const pattern = ajt__make_pattern(reading_part, pitch_type, pitch_num); list_item.insertAdjacentHTML("beforeend", `<span class="ajt__downstep_${pitch_type}">${pattern}</span>`); } return list_item; } function ajt__make_accents_list(ajt_span) { const accents = document.createElement("ul"); for (const accent_group of ajt_span.getAttribute("pitch").split(" ")) { accents.appendChild(ajt__make_accent_list_item(...accent_group.split(":"))); } return accents; } function ajt__make_popup_div(content) { const frame_top = document.createElement("div"); frame_top.classList.add("ajt__frame_title"); frame_top.innerText = "Information"; const frame_bottom = document.createElement("div"); frame_bottom.classList.add("ajt__frame_content"); frame_bottom.appendChild(content); const popup = document.createElement("div"); popup.classList.add("ajt__info_popup"); popup.appendChild(frame_top); popup.appendChild(frame_bottom); return popup; } function ajt__find_word_info_popup(word_span) { return word_span.querySelector(".ajt__info_popup"); } function ajt__find_popup_x_corners(popup_div) { const elem_rect = popup_div.getBoundingClientRect(); const right_corner_x = elem_rect.x + elem_rect.width; return { x_start: elem_rect.x, x_end: right_corner_x, shifted_x_start: elem_rect.x + elem_rect.width / 2, shifted_x_end: right_corner_x + elem_rect.width / 2, }; } function ajt__word_info_on_mouse_enter(word_span) { const popup_div = ajt__find_word_info_popup(word_span); if (popup_div) { ajt__word_info_on_mouse_leave(word_span); const x_pos = ajt__find_popup_x_corners(popup_div); if (x_pos.x_start < 0) { popup_div.classList.add("ajt__left-corner"); popup_div.style.setProperty("--shift-x", `${Math.ceil(-x_pos.x_start)}px`); } else if (x_pos.shifted_x_end < window.innerWidth) { popup_div.classList.add("ajt__in-middle"); } } } function ajt__word_info_on_mouse_leave(word_span) { const popup_div = ajt__find_word_info_popup(word_span); if (popup_div) { popup_div.classList.remove("ajt__left-corner", "ajt__in-middle"); } } function ajt__adjust_popup_position_on_mouse_enter(word_info_span) { word_info_span.addEventListener("mouseenter", (event) => ajt__word_info_on_mouse_enter(event.currentTarget)); word_info_span.addEventListener("mouseleave", (event) => ajt__word_info_on_mouse_leave(event.currentTarget)); } function ajt__format_readings_as_list(readings) { const readings_items = readings.map((reading) => `<li>${reading}</li>`).join(""); const list_elem = document.createElement("ol"); list_elem.classList.add("ajt__readings_list"); list_elem.insertAdjacentHTML("beforeend", readings_items); return list_elem; } function ajt__find_kanji_readings(ruby_tag) { const separators = /[\s;,.、・。]+/iu; const kanji = (ruby_tag.querySelector("rb") || ruby_tag.firstChild).textContent.trim(); const readings = ruby_tag .querySelector("rt") .textContent.split(separators) .map((str) => str.trim()) .filter((str) => str.length); return { kanji: kanji, readings: readings }; } function ajt__reformat_multi_furigana() { const max_inline = 2; document.querySelectorAll("ruby:not(ruby ruby):not(.ajt__furigana_list ruby)").forEach((ruby) => { try { const { kanji, readings } = ajt__find_kanji_readings(ruby); if (readings.length > 1) { ruby.innerHTML = ajt__format_new_ruby(kanji, readings.slice(0, max_inline)); } if (readings.length > max_inline && !ruby.matches(".ajt__word_info ruby")) { const content_ul = ajt__format_readings_as_list(readings); const popup = ajt__make_popup_div(content_ul); const wrapper = document.createElement("span"); ruby.replaceWith(wrapper); wrapper.appendChild(ruby); wrapper.appendChild(popup); wrapper.classList.add("ajt__furigana_list"); ajt__adjust_popup_position_on_mouse_enter(wrapper); } } catch (error) { console.error(error); } }); } function ajt__create_popups() { for (const [idx, span] of document.querySelectorAll(".ajt__word_info").entries()) { if (span.matches(".jpsentence .background *")) { continue; } if (ajt__find_word_info_popup(span)) { continue; } try { const content_ul = ajt__make_accents_list(span); const popup = ajt__make_popup_div(content_ul); popup.setAttribute("ajt__popup_idx", idx); span.setAttribute("ajt__popup_idx", idx); span.appendChild(popup); ajt__adjust_popup_position_on_mouse_enter(span); } catch (error) { console.error(error); } } } function ajt__main() { ajt__create_popups(); ajt__reformat_multi_furigana(); } if (document.readyState === "loading") { document.addEventListener("DOMContentLoaded", ajt__main); } else { ajt__main(); }
</script>"""

CARD_CSS: str = r"""@import url("_ajt_japanese_24.10.8.1.css");
:root {
    /* Color theme */
    --light-mode-bg-color: #fffaf0;
    --light-mode-fg-color: #333333;

    /* Pitch colors */
    --dark-mode-heiban: #39bae6;
    --dark-mode-atamadaka: #ec464f;
    --dark-mode-nakadaka: #ff8f40;
    --dark-mode-odaka: #6cbf43;
    --dark-mode-kifuku: #af85f4;
    --light-mode-heiban: #1aa0ce;
    --light-mode-atamadaka: #e92a35;
    --light-mode-nakadaka: #ff6b03;
    --light-mode-odaka: #61ad3b;
    --light-mode-kifuku: #7e53c4;

    /* Bold color */
    --light-mode-bold: #999999;
    --dark-mode-bold: #7d8590;

    /* PC Font sizes */
    --pc-main-font-size: 16px;
    --pc-main-def-size: 20px;
    --pc-vocab-font-size: 85px;
    --pc-back-vocab-font-size: 60px;
    --pc-sentence-font-size: 52px;
    --pc-back-sentence-font-size: 35px;
    --pc-hint-font-size: 38px;
    --pc-info-font-size: 23px;

    /* Mobile font sizes */
    --mobile-main-font-size: 16px;
    --mobile-main-def-size: 16px;
    --mobile-vocab-font-size: 70px;
    --mobile-back-vocab-font-size: 32px;
    --mobile-sentence-font-size: 38px;
    --mobile-back-sentence-font-size: 24px;
    --mobile-hint-font-size: 24px;
    --mobile-info-font-size: 16px;

    /* Miscellaneous */
    --font-serif: "Georgia", "Liberation Serif", "Times New Roman", "Hiragino Mincho ProN", "Noto Serif CJK JP", "Yu Mincho", HanaMinA, HanaMinB, serif;
    --font-sans: "SF Pro Display", "Liberation Sans", "Segoe UI", "Hiragino Kaku Gothic ProN", "Noto Sans CJK JP", "Meiryo", HanaMinA, HanaMinB, sans-serif;
    --light-mode-image-brightness: 85%;
    --dark-mode-image-brightness: 80%;
    --light-mode-tooltip-hover-color: rgb(256, 256, 256, 0.9);
    --dark-mode-tooltip-hover-color: rgba(0, 0, 0, 0.9);
    --def-picture-size: 200px;
    --max-width: 800px;

    font-size: var(--main-font-size);
}

.card {
    background-color: var(--bg-color) !important;
    color: var(--fg-color) !important;
}

.card.nightMode {
    --bg-color: var(--canvas, #2c2c2c);
    --fg-color: var(--fg, #fcfcfc);
    --heiban: var(--dark-mode-heiban, initial);
    --atamadaka: var(--dark-mode-atamadaka, initial);
    --nakadaka: var(--dark-mode-nakadaka, initial);
    --odaka: var(--dark-mode-odaka, initial);
    --kifuku: var(--dark-mode-kifuku, initial);

    --bg-elevated: rgba(0, 0, 0, 0.12);
    --bg-inset: rgba(255, 255, 255, 0.03);
    --fg-subtle: rgba(255, 255, 255, 0.3);
    --bold: var(--dark-mode-bold, #7d8590);

    --image-brightness: var(--dark-mode-image-brightness);
    --tooltip-hover-color: var(--dark-mode-tooltip-hover-color);
}

.android .nightMode {
    --bg-color: black;
    --fg-color: white;
}

.android .nightMode:not(.ankidroid_dark_mode) {
    /* make it brighter since bg is black */
    --bg-elevated: rgba(255, 255, 255, 0.06);
}

.android .nightMode.ankidroid_dark_mode {
    --bg-color: #303030;
}

.card:not(.nightMode) {
    --bg-color: var(--light-mode-bg-color);
    --fg-color: var(--light-mode-fg-color);
    --heiban: var(--light-mode-heiban, initial);
    --atamadaka: var(--light-mode-atamadaka, initial);
    --nakadaka: var(--light-mode-nakadaka, initial);
    --odaka: var(--light-mode-odaka, initial);
    --kifuku: var(--light-mode-kifuku, initial);

    --bg-elevated: rgba(0, 0, 0, 0.03);
    --bg-inset: rgba(0, 0, 0, 0.06);
    --fg-subtle: rgba(0, 0, 0, 0.6);
    --bold: var(--light-mode-bold, #999999);

    --image-brightness: var(--light-mode-image-brightness);
    --tooltip-hover-color: var(--light-mode-tooltip-hover-color);
}

html.win,
html.mac,
html.linux:not(.android) {
    --main-font-size: var(--pc-main-font-size);
    --main-def-size: var(--pc-main-def-size);
    --vocab-font-size: var(--pc-vocab-font-size);
    --back-vocab-font-size: var(--pc-back-vocab-font-size);
    --sentence-font-size: var(--pc-sentence-font-size);
    --back-sentence-font-size: var(--pc-back-sentence-font-size);
    --hint-font-size: var(--pc-hint-font-size);
    --info-font-size: var(--pc-info-font-size);
}

html.mobile {
    --main-font-size: var(--mobile-main-font-size);
    --main-def-size: var(--mobile-main-def-size);
    --vocab-font-size: var(--mobile-vocab-font-size);
    --back-vocab-font-size: var(--mobile-back-vocab-font-size);
    --sentence-font-size: var(--mobile-sentence-font-size);
    --back-sentence-font-size: var(--mobile-back-sentence-font-size);
    --hint-font-size: var(--mobile-hint-font-size);
    --info-font-size: var(--mobile-info-font-size);
}

#qa {
    display: flex;
    align-items: stretch;
    flex-direction: column;
    min-height: calc(100vh - 40px);
    font-family: var(--font-serif);
    font-size: var(--main-font-size);
    text-align: center;
}

/* ------- Mobile css ------- */
@media (max-width: 512px) {
    .images-container {
        justify-content: space-around;
        flex-direction: row !important;
        max-width: 100% !important;
        width: 100%;
        flex-wrap: wrap;
    }

    .images-container img {
        width: 44%;
    }
}

/* ----- Front elements ----- */

.front-vocab {
    #font-size: var(--vocab-font-size);
    line-height: 1.5;
		white-space: nowrap;
		font-size: 12vw;

}

.front-vocab rt{
    visibility: hidden;
}

.front-sentence {
    font-size: var(--sentence-font-size);
    display: inline-block;
    line-height: 1.5;
}

#hint {
    font-size: var(--hint-font-size);
    margin-top: -5px;
    line-height: 1.5;
}

#click {
    user-select: none;
}

#click .front-vocab {
    display: inline-block;
    line-height: 1.2;
    margin-bottom: 20px;
    border-bottom: 2px dotted var(--fg-subtle);
}

/* ----- Back elements ----- */

/* Vocab on the back (for mobile) */
.vocab {
    line-height: 1.5;
    font-size: var(--back-vocab-font-size);
}

a {
    color: #3b82f6 !important;
}

.nightMode a {
    color: #93c5fd !important;
}

/* Header */
header {
    color: var(--fg-subtle);
    height: 40px;
    text-align: right;
    width: 100%;
    font-size: 1rem;
}

.top-container {
    max-width: calc(var(--max-width) + 20px);
    margin: 0px auto;
    width: calc(100% - 20px);
    fill: var(--fg-subtle) !important;
    position: relative;
    display: inline-block;
}

.freq-dropdown {
    cursor: pointer;
}

.freq-list-container {
    font-family: var(--font-sans);
    display: none;
    position: absolute;
    top: 100%;
    right: 0;
    background-color: var(--tooltip-hover-color);
    color: var(--fg-color);
    padding: 10px;
    border-radius: 5px;
    z-index: 1000;
    width: 200px;
}

.freq-list-container ul {
    list-style-type: none;
    line-height: 1.5;
    margin: 0;
    padding: 0;
}

.freq-dropdown:hover .freq-list-container {
    display: block;
}

/* Info (audio, reading) */
.info {
    font-family: var(--font-sans);
    font-size: var(--info-font-size);
    color: var(--fg-color);
}

.mobile .info {
    font-size: 0.9rem;
    padding-top: 7px;
}

/* Replay button */
.replay-button svg {
    width: 32px;
    height: 32px;
}

.mobile .audio-buttons {
    position: fixed;
    bottom: 0;
    left: 0;
    z-index: 1000;
}

/* Pitch */
.pitch {
    display: inline;
}

#pitch-tags {
    color: var(--bg-color);
    font-family: var(--font-serif);
    background-color: var(--fg-color);
    display: none;
    vertical-align: top;
    padding: 1px 3px;
    margin-right: -5px;
}

.mobile .nightMode #pitch-tags {
    color: #000 !important;
    background-color: #fff;
}

/* When multiple pitch */
.pitch ul,
#pitch-tags ul {
    list-style: none;
    display: inline;
    margin: 0;
    padding: 0;
}

.pitch li,
#pitch-tags li {
    display: inline;
}

.pitch ul>li:not(:last-child)::after,
#pitch-tags ul>li:not(:last-child)::after {
    content: "・";
}

.pitch ul>li:not(:last-child)::after {
    color: var(--fg-color);
}

#pitch-tags ul>li:not(:last-child)::after {
    color: var(--bg-color);
}

/* Definition container */
.main-def {
    max-width: var(--max-width);
    font-size: var(--main-def-size);
    line-height: 1.75em;
    margin: 25px auto;
    width: calc(100% - 20px);
    position: relative;
    display: block;
}

/* Definition info display */
.def-info-container {
    display: block;
    max-width: var(--max-width);
    width: calc(100% - 20px);
    position: relative;
    margin: 0 auto;
}

.def-info {
    font-family: var(--font-sans);
    position: absolute;
    top: 0;
    right: 0;
    font-size: 0.9rem;
    color: var(--fg-subtle);
    pointer-events: none;
}

.mobile .def-info {
    display: none;
}

/* MainDefinition */
.definition {
    text-align: left;
    width: fit-content;
    max-width: 100%;
}

/* Definition box */
.def-blockquote {
    font-family: var(--font-sans);
    background-color: var(--bg-elevated);
    display: block;
    max-width: min(var(--max-width), calc(100% - 20px));
    text-align: left;
    align-items: left;
    justify-content: left;
    border-left: 5px solid #ccc;
    overflow: hidden;
    padding: 5px 10px;
    position: relative;
}

/* Primary Image */
.image img {
    max-height: 400px;
    width: auto;
    border-radius: 5px;
    cursor: pointer;
    transition: filter 0.3s;
}

.image img:hover,
.def-image img:hover {
    filter: brightness(var(--image-brightness));
}

/* Definition Image(s) */
.def-image {
    float: right;
    margin-left: 10px;
    max-width: min(35%, var(--def-picture-size));
    display: flex;
    flex-flow: column nowrap;
    justify-content: flex-start;
    gap: 10px;
}

.def-image img {
    object-fit: contain;
    max-height: var(--def-picture-size);
    border-radius: 3px;
    cursor: pointer;
    transition: filter 0.3s;
}

.def-image ol {
    list-style-type: none;
    padding: 0;
    margin: 0;
}

/* Image modal css */
.modal-bg {
    position: fixed;
    display: none;
    top: 0;
    right: 0;
    bottom: 0;
    left: 0;
    background-color: rgba(0, 0, 0, 0.8);
    z-index: 1000;
    cursor: pointer;
}

.img-popup-container {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: min(calc(100% - 20px), calc(var(--max-width) + 200px));
    display: none;
    z-index: 1001;
    overflow: hidden;
}

.img-popup-img {
    width: auto;
    height: auto;
    margin: 0 auto;
}

/* Hide NFSW Images -- make sure you use the tag `NSFW` EXACTLY */
.NSFW img {
    filter: blur(30px);
    transition: filter 0.2s;
}

.NSFW img:hover {
    filter: blur(0px);
    transition: filter 0.2s;
}

/* Back sentence */
.sentence {
    line-height: 1.5;
    font-size: var(--back-sentence-font-size);
    display: inline-block;
    width: calc(100% - 20px);
    max-width: var(--max-width);
}

.sentence-mobile {
    display: none;
}

.mobile .sentence {
    display: none;
}

.mobile .sentence-mobile {
    line-height: 1.5;
    font-size: var(--back-sentence-font-size);
    display: inline-block;
    width: calc(100% - 20px);
    max-width: var(--max-width);
}

/* Footer */
footer {
    margin-top: auto;
    width: 100%;
}

.bot-container {
    display: flex;
    justify-content: flex-end;
    max-width: calc(var(--max-width) + 20px);
    margin: 0px auto;
    width: calc(100% - 20px);
}

.tags-container {
    flex-grow: 1;
}

.tags-container .tags {
    min-height: 1.6em;
}

.tags {
    font-family: var(--font-sans);
    background-color: var(--bg-elevated);
    color: var(--fg-color);
    display: inline-grid;
    place-items: center;
    padding: 1px 5px;
    cursor: pointer;
    border-radius: 5px;
    font-size: 0.9rem;
    margin: auto 3px;
    text-overflow: ellipsis;
    overflow: hidden;
    max-width: 60dvw;
    white-space: nowrap;
}

.mobile .tags {
    padding: 1px 3px;
    font-size: 9px;
}

/* Popup CSS */
.popup {
    font-family: var(--font-sans);
    background-color: var(--bg-elevated);
    display: block;
    border-radius: 8px;
    padding: 10px;
    max-width: min(var(--max-width), calc(100% - 20px));
}

/* Definition Header */
.def-header {
    display: flex;
    font-size: 30px;
    justify-content: center;
    align-items: center;
    max-width: 820px;
    margin: auto;
    position: relative;
}

.dh-left {
    /* left */
    background: var(--bg-elevated);
    padding: 0.52em;
    border-radius: 5px;
    flex: 1;
    /* takes up all available space */
}

.dh-right {
    padding-left: 20px;
    max-width: 400px;
    position: relative;
    font-size: 0;
    /* weird hack needed to make the image stay in line with the .def-header */
}

.mobile .dh-left {
    background: var(--bg-elevated);
    padding: 0.2em;
    padding-top: 0.2em;
    padding-bottom: 0.2em;
    border-radius: 10px;
    max-width: 600vw;
		white-space: nowrap;
}

.mobile .dh-right {
    max-width: 40vw;
}

/* Misc. info */
.misc-info {
    margin: 0 auto;
}

.misc-info ul {
    margin: 0;
}

/* ----- Misc ----- */

/* Furigana */
.show-furigana>ruby rt {
    visibility: visible;
}

ruby rt {
    user-select: none;
    visibility: hidden;
}

ruby:hover rt {
    visibility: visible;
}

/* Bold */
b {
    color: var(--bold);
    font-weight: 600;
}

b>ruby rt {
    opacity: 1;
}

.mobile b {
    font-weight: 400;
}

/* Dropdown */
details {
    font-family: var(--font-sans);
    margin: 5px 0px;
}

summary {
    user-select: none;
    cursor: pointer;
    margin: 0px auto;
}

/* Pitch graphs css */
.pitch-low {
    position: relative;
}

.pitch-high {
    position: relative;
}

.pitch-high>.pitch-line {
    display: block;
    position: absolute;
    top: -0.1em;
    left: 0;
    right: 0;
    height: 0;
    border-top-width: 0.1em;
    border-top-style: solid;
}

.pitch-to-drop {
    position: relative;
    padding-right: 0.1em;
    margin-right: 0.1em;
}

.pitch-to-drop>.pitch-line {
    display: block;
    position: absolute;
    top: -0.1em;
    left: 0;
    right: 0;
    border-top-width: 0.1em;
    border-top-style: solid;
    right: -0.1em;
    height: 0.4em;
    border-right-width: 0.1em;
    border-right-style: solid;
}

/* Pitch coloring */
.heiban {
    color: var(--heiban);
}

.atamadaka {
    color: var(--atamadaka);
}

.nakadaka {
    color: var(--nakadaka);
}

.odaka {
    color: var(--odaka);
}

.kifuku {
    color: var(--kifuku);
}

/* Definition toggle css */
.left-edge,
.right-edge {
    position: absolute;
    top: 0;
    width: 50px;
    height: 100%;
    cursor: pointer;
    opacity: 0.4;
}

.left-edge {
    left: 0;
    border-radius: 8px 0px 0px 8px;
}

.right-edge {
    right: 0;
    border-radius: 0px 8px 8px 0px;
}

.left-edge:hover,
.right-edge:hover {
    background-color: var(--bg-inset);
    cursor: pointer;
}

/* Format Definitions */
ul[data-sc-content="glossary"]>li:not(:first-child)::before {
    white-space: pre-wrap;
    content: " | ";
    display: inline;
}

ul[data-sc-content="glossary"]>li {
    display: inline;
}

ul[data-sc-content="glossary"] {
    display: inline;
    list-style: none;
    padding-left: 0;
}

/* reduce indentations of Jitendex for mobile */
.mobile li[data-dictionary^="Jitendex"] ul,
.mobile li[data-dictionary^="Jitendex"] ol,
.mobile li[data-details^="Jitendex"] ul,
.mobile li[data-details^="Jitendex"] ol {
    padding-left: 0.3em;
}

/* Turn off italics */
.definition i {
    font-style: normal;
}

li[data-dictionary^="JMdict"] i {
    font-style: italic;
}

.definition a span {
    max-width: 300px !important;
}

.definition .hidden {
    display: none
}

/* Prevent wrapping in the middle of a Jitendex tags */
span[data-sc-code] {
    white-space: nowrap;
}

/* backwards compatibility code for JPMN definitions */

li[data-details="JMdict (English)"] .dict-group__glossary>ul,
li[data-details="JMdict (English)"] .dict-group__glossary ul[data-sc-content="glossary"],
li[data-details="JMdict"] .dict-group__glossary>ul,
li[data-details="JMdict"] .dict-group__glossary ul[data-sc-content="glossary"],
li[data-details="JMdict Extra"] .dict-group__glossary>ul,
li[data-details="JMdict Extra"] .dict-group__glossary ul[data-sc-content="glossary"] {
    display: inline;
    padding-left: 0em;
}

li[data-details="JMdict (English)"] .dict-group__glossary>ul>li,
li[data-details="JMdict (English)"] .dict-group__glossary ul[data-sc-content="glossary"]>li,
li[data-details="JMdict"] .dict-group__glossary>ul>li,
li[data-details="JMdict"] .dict-group__glossary ul[data-sc-content="glossary"]>li,
li[data-details="JMdict Extra"] .dict-group__glossary>ul>li,
li[data-details="JMdict Extra"] .dict-group__glossary ul[data-sc-content="glossary"]>li {
    display: inline;
    padding-right: 0em;
    margin-right: 0em;
}

li[data-details="JMdict (English)"] .dict-group__glossary>ul>li::after,
li[data-details="JMdict (English)"] .dict-group__glossary ul[data-sc-content="glossary"]>li::after,
li[data-details="JMdict"] .dict-group__glossary>ul>li::after,
li[data-details="JMdict"] .dict-group__glossary ul[data-sc-content="glossary"]>li::after,
li[data-details="JMdict Extra"] .dict-group__glossary>ul>li::after,
li[data-details="JMdict Extra"] .dict-group__glossary ul[data-sc-content="glossary"]>li::after {
    content: " | ";
    white-space: pre-wrap;
}

li[data-details="JMdict (English)"] .dict-group__glossary>ul>li:last-of-type:after,
li[data-details="JMdict (English)"] .dict-group__glossary ul[data-sc-content="glossary"]>li:last-of-type:after,
li[data-details="JMdict"] .dict-group__glossary>ul>li:last-of-type:after,
li[data-details="JMdict"] .dict-group__glossary ul[data-sc-content="glossary"]>li:last-of-type:after,
li[data-details="JMdict Extra"] .dict-group__glossary>ul>li:last-of-type:after,
li[data-details="JMdict Extra"] .dict-group__glossary ul[data-sc-content="glossary"]>li:last-of-type:after {
    display: none;
}

/*
 * customization for specific dictionaries
 */
/* Makes JMdict italic */
ol li[data-details="JMdict (English)"] .dict-group__tag-list,
ol li[data-details="JMdict"] .dict-group__tag-list,
ol li[data-details="JMdict Extra"] .dict-group__tag-list {
    font-style: italic;
}

/* removes the dictionary entry for jmdict */
ol li[data-details="JMdict (English)"] .dict-group__tag-list .dict-group__tag--dict,
ol li[data-details="JMdict"] .dict-group__tag-list .dict-group__tag--dict,
ol li[data-details="JMdict Extra"] .dict-group__tag-list .dict-group__tag--dict {
    display: none;
}

/* Makes Nico/Pixiv italic */
ol li[data-details="Nico/Pixiv"] .dict-group__tag-list {
    font-style: italic;
}

/* Removes the extra text for the collapsed 新和英 display */
ol li[data-details="新和英"] details.glossary-text__details .glossary-text__summary .dict-group__glossary--first-line {
    display: none;
}

/*
 * --------------------
 *  dictionary entries
 * --------------------
 */
.dict-group__tag-list .dict-group__tag:not(:first-child)::before {
    content: ", ";
}

.dict-group__tag-list::before {
    content: "(";
}

.dict-group__tag-list::after {
    content: ") ";
}

/* Show definition furigana */
.def-blockquote rt {
    visibility: hidden;
}

/* Lessen def-blockquote padding */
.def-blockquote {
    padding-block: .5em;
}
.def-blockquote ol {
    margin-block: 0em;
}
.definition ol:has(> li[data-dictionary]),
.definition ol:has(> li[data-details]) {
    padding-inline-start: 1.3em;
}

/* Removes list numbering when only one list element  */
.definition ol:has(> li[data-dictionary]:only-of-type),
.definition ol:has(> li[data-details]:only-of-type) {
    list-style-type : none;
    padding-inline-start: 0;
}

"""
