const NOTICIAS_API_URL = "https://portal-imigrante-pt.onrender.com/api/noticias";

async function carregarNoticiasAoVivo() {
    const container = document.getElementById("contentor-noticias");
    if (!container) return; 

    try {
        const response = await fetch(NOTICIAS_API_URL);
        const data = await response.json();

        if (data.noticias && data.noticias.length > 0) {
            container.innerHTML = ""; // Limpa os cards antigos/estáticos

            data.noticias.forEach(noticia => {
                // Injeta os novos cards gerados pelo teu main.py com o Tavily
                container.innerHTML += `
                    <div class="card-noticia" style="margin-bottom: 20px; padding: 15px; border-left: 4px solid #0056b3; background: #f9f9f9;">
                        <img src="${noticia.imagem}" alt="${noticia.titulo}" style="width: 100%; max-height: 150px; object-fit: cover; border-radius: 4px;">
                        <span class="tag" style="display: inline-block; background: #0056b3; color: white; padding: 2px 8px; font-size: 11px; border-radius: 3px; margin-top: 8px;">${noticia.tag}</span>
                        <h3 style="margin: 5px 0; font-size: 16px;"><a href="${noticia.url}" target="_blank" style="color: #333; text-decoration: none; font-weight: bold;">${noticia.titulo}</a></h3>
                        <p style="font-size: 13px; color: #555;">${noticia.resumo}</p>
                    </div>
                `;
            });
        }
    } catch (error) {
        console.error("Erro ao carregar notícias do Render:", error);
    }
}

// Executa a função assim que a página abrir
document.addEventListener("DOMContentLoaded", carregarNoticiasAoVivo);