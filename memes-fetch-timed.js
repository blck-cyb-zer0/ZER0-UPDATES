        const memesStartTime = Date.now();
        fetch('memes.json')
            .then(res => res.json())
            .then(data => {
                const elapsed = Date.now() - memesStartTime;
                const remaining = Math.max(0, 700 - elapsed);
                setTimeout(() => {
                    document.getElementById('memes-container').innerHTML = data.memes.map(m => `
                        <div class="meme-card">
                            <img src="${m.image}" alt="meme">
                            <div class="meme-caption">${m.caption}</div>
                        </div>
                    `).join('');
                    document.getElementById('memes-container').classList.add('fade-in');
                }, remaining);
            })
            .catch(() => {
                document.getElementById('memes-container').innerText = 'Failed to load memes.';
            });
