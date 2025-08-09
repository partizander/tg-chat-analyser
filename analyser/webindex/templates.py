# chatviz/webindex/templates.py

CSS = """
body {
    font-family: Arial, sans-serif;
    margin: 20px;
    text-align: center;
}
img {
    max-width: 80%;
    height: auto;
    cursor: pointer;
    border: 1px solid #ccc;
    margin: 15px 0;
    transition: transform 0.2s ease-in-out;
}
img:hover {
    transform: scale(1.02);
}
#lightbox {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.9);
    display: none;
    justify-content: center;
    align-items: center;
    z-index: 9999;
}
#lightbox img {
    max-width: 95%;
    max-height: 95%;
    object-fit: contain;
    box-shadow: 0 0 25px rgba(0,0,0,0.8);
}
"""

JS = """
document.querySelectorAll('img').forEach(img => {
    img.addEventListener('click', () => {
        const lightbox = document.getElementById('lightbox');
        const lightboxImg = document.getElementById('lightbox-img');
        lightboxImg.src = img.src;
        lightbox.style.display = 'flex';
    });
});
document.getElementById('lightbox').addEventListener('click', () => {
    document.getElementById('lightbox').style.display = 'none';
});
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        document.getElementById('lightbox').style.display = 'none';
    }
});
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Chat Analysis Results</title>
<style>
{css}
</style>
</head>
<body>
<h1>Chat Analysis Results</h1>
{content}
<div id="lightbox">
    <img id="lightbox-img" src="" alt="Enlarged view">
</div>
<script>
{js}
</script>
</body>
</html>
"""
