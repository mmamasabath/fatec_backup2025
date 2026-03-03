let forma1 = {
    base: 15,
    altura: 12,
    tipo: 'R', // Retângulo
    nome: 'Retângulo'
}

let forma2 = {
    base: 10,
    altura: 26,
    tipo: 'T', // Triângulo
    nome: 'Triângulo'
}

let forma3 = {
    base: 20,
    altura: 10,
    tipo: 'E', // Elipse
    nome: 'Elipse'
}

let forma4 = {
    base: 7.5,
    altura: 12.3,
    tipo: 'G', // ???
    nome: 'não existe'
}

let forma5 = {
    base: 'batata',
    altura: 'cebola',
    tipo: 'E',
    nome: 'legumes'
}

function calcularArea(forma) {
    switch(forma.tipo){
        case 'R': // Retângulo
            return forma.base * forma.altura
        case 'T': // Triângulo
            return forma.base * forma.altura / 2
        case 'E': // Elipse
            return (forma.base / 2) * (forma.altura / 2) * Math.PI
        default:
            return null
    }
}
console.log(`Área de um ${forma1.nome} de ${forma1.base}x${forma1.altura}: ${calcularArea(forma1)} `)
console.log(`Área de um ${forma2.nome} de ${forma2.base}x${forma2.altura}: ${calcularArea(forma2)} `)
console.log(`Área de um ${forma3.nome} de ${forma3.base}x${forma3.altura}: ${calcularArea(forma3)} `)
console.log(`Área de um ${forma4.nome} de ${forma4.base}x${forma4.altura}: ${calcularArea(forma4)} `)
console.log(`Área de um ${forma5.nome} de ${forma5.base}x${forma5.altura}: ${calcularArea(forma5)} `)
