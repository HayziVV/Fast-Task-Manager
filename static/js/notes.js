const editor = document.getElementById('richTextEditor');
const container = document.getElementById('editorContainer');
const hiddenInput = document.getElementById('hiddenContentInput');

function changeFontSize(size) {
    const selection = window.getSelection();
    if (!selection.rangeCount) return;

    const range = selection.getRangeAt(0);

    if (!editor.contains(range.commonAncestorContainer)) {
        console.warn("Bloqueado: Tentativa de formatação fora da área do documento.");
        return;
    }

    if (!range.collapsed) {
        const span = document.createElement("span");
        span.style.fontSize = size;
        span.style.display = "inline-block";

        try {
            span.appendChild(range.extractContents());
            range.insertNode(span);

            selection.removeAllRanges();
            const newRange = document.createRange();
            newRange.selectNodeContents(span);
            selection.addRange(newRange);
        } catch (e) {
            console.error(e);
        }
    } else {
        const span = document.createElement("span");
        span.style.fontSize = size;


        const zeroWidthSpaceNode = document.createTextNode("\u200B");
        span.appendChild(zeroWidthSpaceNode);

        range.insertNode(span);

        const newRange = document.createRange();
        newRange.setStart(zeroWidthSpaceNode, 1);
        newRange.setEnd(zeroWidthSpaceNode, 1);
        selection.removeAllRanges();
        selection.addRange(newRange);
    }

    synchronizeEditorContents();
}


function exportToPDF() {
    const printableClone = editor.cloneNode(true);

    printableClone.style.color = '#111827';
    printableClone.style.backgroundColor = '#ffffff';
    printableClone.style.padding = '30px';
    printableClone.style.width = '100%';

    const children = printableClone.getElementsByTagName('*');
    for (let i = 0; i < children.length; i++) {
        children[i].style.color = '#111827';
    }

    const opt = {
        margin: 15,
        filename: 'documento_nota.pdf',
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2, backgroundColor: '#ffffff', logging: false },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
    };

    html2pdf().set(opt).from(printableClone).save();
}

function updateGlobalFont(fontClass) {
    editor.classList.remove('font-sans', 'font-serif', 'font-mono');
    editor.classList.add(fontClass);
}

function toggleFullWidth(isFullWidth) {
    if (isFullWidth) {
        container.classList.add('full-width-active');
    } else {
        container.classList.remove('full-width-active');
    }
}

function synchronizeEditorContents() {
    hiddenInput.value = editor.innerHTML;
}