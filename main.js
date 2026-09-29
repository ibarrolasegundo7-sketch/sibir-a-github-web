// 15/9 ultima modificacion
// segundo ibarrola
const juegoContent = document.querySelector('.juego-content');
const sudoku = document.getElementById('juegoContent');
const oportunidades = document.querySelector('.oportunidades');
const card_form = document.querySelector('.card-form')
let vidas = Number(localStorage.getItem("vidas") ?? 3);

card_form.style.display = "none"

tablero = [
    ["", "", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", "", ""]
]

// 22/9 ultima modificacion
// segundo ibarrola
function comprobarNumero(x, y, num) {

    // Revisar fila
    for (let i = 0; i < 9; i++) {
        if (tablero[x][i] == num) {
            return false;
        }
    }

    // Revisar columna
    for (let i = 0; i < 9; i++) {
        if (tablero[i][y] == num) {
            return false;
        }
    }

    // Revisar bloque 3x3
    let inicioFila = Math.floor(x / 3) * 3;
    let inicioColumna = Math.floor(y / 3) * 3;

    for (let i = inicioFila; i < inicioFila + 3; i++) {
        for (let j = inicioColumna; j < inicioColumna + 3; j++) {
            if (tablero[i][j] == num) {
                return false;
            }
        }
    }

    return true;
}

function generarSudoku() {

    function resolver() {

        for (let i = 0; i < 9; i++) {
            for (let j = 0; j < 9; j++) {

                if (tablero[i][j] == "") {

                    let intentos = 0;

                    while (intentos < 9) {

                        let randomNum = Math.floor(Math.random() * 9) + 1;

                        if (comprobarNumero(i, j, randomNum)) {

                            tablero[i][j] = randomNum;

                            if (resolver()) {
                                return true;
                            }

                            tablero[i][j] = "";
                        }

                        intentos++;
                    }

                    return false;
                }
            }
        }

        return true;
    }

    resolver();
}


function mostrarCelda(){
    return Math.random() < 0.6;
}

function mostrarSudoku() {
    for (let i = 0; i < 9; i++) {
        let div = document.createElement('div');
        div.className = 'blok';

        let fila = Math.floor(i / 3) * 3;
        let columna = (i % 3) * 3;

        for (let j = 0; j < 3; j++) {
            for (let k = 0; k < 3; k++) {

                if (mostrarCelda()){

                    let input = document.createElement('input');
                    input.type = 'text';
                    input.maxLength = 1;
                    input.className = 'celda';

                    input.dataset.x = fila + j
                    input.dataset.y = columna + k
    
                    input.value = "";
    
                    div.appendChild(input);
                }
                else {

                    let label = document.createElement("label")
                    num = tablero[fila + j][columna + k]
                    label.textContent = num.toString();
                    label.className = 'celda'
                    div.appendChild(label)
                }
                
            }
        }

        sudoku.appendChild(div);
    }
}

generarSudoku();
mostrarSudoku();

// logica para jugar
// 22/9 creacion

function intentos(vida){
    oportunidades.textContent = "vidas: " + vida
    localStorage.setItem("vidas", vida);

    if (localStorage.getItem("pagar") == "si"){
        card_form.style.display = "block"
    }
    else if (vida <= 0){
        localStorage.setItem("pagar", "si");
        card_form.style.display = "block"
    }
}

sudoku.addEventListener("input", function(event) {
    let e = event.target;

    let x = e.dataset.x;
    let y = e.dataset.y;

    if (e.value == tablero[x][y]) {
        let label = document.createElement("label")
        label.className = 'celda'
        label.textContent = tablero[x][y]

        e.parentNode.replaceChild(label, e);
    } else {
        e.className = "celda mal"
        vidas--
        intentos(vidas)
    }
});

intentos(vidas)