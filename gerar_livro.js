const fs = require('fs');
const path = require('path');

// Verifica argumentos
if (process.argv.length < 3) {
    console.log("Uso: node gerar_livro.js <Nome_da_Pasta_do_Ano>");
    console.log("Exemplo: node gerar_livro.js 7o_Ano");
    process.exit(1);
}

const ano = process.argv[2];
const baseDir = path.join(__dirname, 'Acutis', 'Novo_Padrao', ano);

if (!fs.existsSync(baseDir)) {
    console.error(`Erro: O diretório ${baseDir} não existe.`);
    process.exit(1);
}

// Lê os arquivos da pasta e ordena por número da aula
const files = fs.readdirSync(baseDir).filter(f => f.startsWith('Aula_') && f.endsWith('.md'));
files.sort((a, b) => {
    const numA = parseInt(a.replace(/\D/g, ''));
    const numB = parseInt(b.replace(/\D/g, ''));
    return numA - numB;
});

let conteudoLivro = `# Livro Didático - Português (${ano.replace('_', ' ')})\n\n`;
let conteudoGabarito = `# Gabarito Completo\n\n`;

for (const file of files) {
    const filePath = path.join(baseDir, file);
    let content = fs.readFileSync(filePath, 'utf8');

    // Extrair o título da aula (normalmente a primeira linha com #)
    let aulaTitle = `Respostas da ${file}`;
    const titleMatch = content.match(/^#\s+(.+)$/m);
    if (titleMatch) {
        aulaTitle = `Respostas: ${titleMatch[1]}`;
    }

    let aulaGabarito = `## ${aulaTitle}\n\n`;
    let temGabarito = false;

    // Remove fallback antigos caso existam
    content = content.replace(/^[ \t]*\*?[ \t]*\*\*Gabarito.*\r?\n?/gim, '');

    // Processa as tags de gabarito
    const gabaritoRegex = /<!-- INICIO_GABARITO -->([\s\S]*?)<!-- FIM_GABARITO -->/g;
    
    // Substitui cada gabarito, salvando o conteúdo para o capítulo final
    content = content.replace(gabaritoRegex, (match, gabaritoContent) => {
        temGabarito = true;
        // Limpa marcações markdown para não bugar a lista (opcional, manter o formato)
        aulaGabarito += gabaritoContent.trim() + '\n\n';
        return ''; // Remove do conteúdo principal
    });

    if (temGabarito) {
        conteudoGabarito += aulaGabarito + '---\n\n';
    }

    conteudoLivro += content + '\n\n<div style="page-break-after: always;"></div>\n\n';
}

// Junta as duas partes
const livroFinal = conteudoLivro + conteudoGabarito;
const outputPath = path.join(__dirname, `Livro_${ano}.md`);

fs.writeFileSync(outputPath, livroFinal);
console.log(`✅ Livro gerado com sucesso em: ${outputPath}`);
