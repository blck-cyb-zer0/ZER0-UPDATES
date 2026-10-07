        (function() {
            const currentPage = location.pathname.split('/').pop().replace('.html', '') || 'index';
            const pages = ['index', 'deals', 'memes', 'coupons'];
            pages.forEach(page => {
                const updated = localStorage.getItem(page + '-last-updated');
                const visited = localStorage.getItem(page + '-last-visited');
                const dot = document.querySelector('.zer0-nav-dot[data-page="' + page + '"]');
                if (dot && updated && (!visited || parseInt(updated) > parseInt(visited))) {
                    dot.classList.add('show');
                }
            });
            localStorage.setItem(currentPage + '-last-visited', Date.now());
        })();
