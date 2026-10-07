        const dealsStartTime = Date.now();
        fetch('deals.json')
            .then(res => res.json())
            .then(data => {
                const elapsed = Date.now() - dealsStartTime;
                const remaining = Math.max(0, 700 - elapsed);
                setTimeout(() => {
                    allDeals = data.deals;
                    buildFilters(allDeals);
                    renderDeals(allDeals);
                    document.getElementById('deals-container').classList.add('fade-in');
                }, remaining);
            })
            .catch(() => {
                document.getElementById('deals-container').innerText = 'Failed to load deals.';
            });
