// Mermaid initialization for markdown documentation
// Only activates on /docs page to avoid interfering with Dash callbacks

(function() {
    let mermaidLoaded = false;

    function loadMermaid(callback) {
        if (mermaidLoaded) {
            if (typeof mermaid !== 'undefined') callback();
            return;
        }

        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js';
        script.onload = function() {
            mermaidLoaded = true;
            callback();
        };
        script.onerror = function() {
            console.error('Failed to load Mermaid');
        };
        document.head.appendChild(script);
    }

    function getThemeConfig() {
        const isDark = document.documentElement.getAttribute('data-mantine-color-scheme') === 'dark';

        return {
            startOnLoad: false,
            theme: isDark ? 'dark' : 'default',
            themeVariables: isDark ? {
                primaryColor: '#a78bfa',
                primaryTextColor: '#ffffff',
                primaryBorderColor: '#6b5b95',
                lineColor: '#c8c8d8',
                secondaryColor: '#1a1a24',
                tertiaryColor: '#0d0d12',
                background: '#1a1a24',
                mainBkg: '#1a1a24',
                nodeBorder: '#a78bfa',
                clusterBkg: '#22222e',
                titleColor: '#a78bfa',
                edgeLabelBackground: '#1a1a24'
            } : {
                primaryColor: '#7c3aed',
                primaryTextColor: '#1e1b2e',
                primaryBorderColor: '#d8b4fe',
                lineColor: '#4a4760',
                secondaryColor: '#f5f3f7',
                tertiaryColor: '#faf9fb',
                background: '#ffffff',
                mainBkg: '#ffffff',
                nodeBorder: '#7c3aed',
                clusterBkg: '#f8f7fa',
                titleColor: '#7c3aed',
                edgeLabelBackground: '#ffffff'
            }
        };
    }

    function renderMermaidDiagrams() {
        if (typeof mermaid === 'undefined') {
            console.warn('Mermaid not loaded yet');
            return;
        }

        // Re-initialize mermaid with current theme
        mermaid.initialize(getThemeConfig());

        // Find all code blocks
        const codeBlocks = document.querySelectorAll('.markdown-body pre code');
        console.log('Found code blocks:', codeBlocks.length);

        let diagramCount = 0;

        codeBlocks.forEach(function(code, index) {
            const pre = code.parentElement;

            // Skip if already processed
            if (pre.dataset.mermaidProcessed === 'true') return;

            const text = code.textContent.trim();

            // Check if it's a mermaid diagram by content
            const mermaidKeywords = [
                'flowchart', 'graph', 'sequenceDiagram', 'classDiagram',
                'stateDiagram', 'erDiagram', 'gantt', 'pie', 'journey',
                'gitGraph', 'mindmap', 'timeline', 'quadrantChart'
            ];

            const isMermaid = mermaidKeywords.some(keyword =>
                text.startsWith(keyword + ' ') ||
                text.startsWith(keyword + '\n') ||
                text === keyword
            );

            // Also check for language-mermaid class
            const hasClass = code.className.includes('mermaid') ||
                           code.className.includes('language-mermaid');

            if (isMermaid || hasClass) {
                console.log('Found mermaid diagram:', index, text.substring(0, 50));

                pre.dataset.mermaidProcessed = 'true';
                diagramCount++;

                // Create unique ID
                const id = 'mermaid-' + Date.now() + '-' + index;

                // Create container
                const container = document.createElement('div');
                container.className = 'mermaid';
                container.id = id;
                container.textContent = text;

                // Replace pre with container
                pre.parentNode.replaceChild(container, pre);
            }
        });

        console.log('Mermaid diagrams to render:', diagramCount);

        if (diagramCount > 0) {
            // Run mermaid on unprocessed diagrams
            setTimeout(function() {
                try {
                    mermaid.run({
                        querySelector: '.mermaid:not([data-processed])'
                    });
                } catch (e) {
                    console.error('Mermaid render error:', e);
                }
            }, 100);
        }
    }

    function checkAndRender() {
        // Only proceed on docs page
        if (!window.location.pathname.startsWith('/docs')) return;

        console.log('Checking for mermaid diagrams on /docs');

        loadMermaid(function() {
            console.log('Mermaid loaded, rendering...');
            setTimeout(renderMermaidDiagrams, 300);
        });
    }

    // Initial check after page load
    function init() {
        setTimeout(checkAndRender, 500);

        // Watch for URL changes (Dash SPA navigation)
        let lastPath = window.location.pathname;
        setInterval(function() {
            const currentPath = window.location.pathname;
            if (currentPath !== lastPath) {
                lastPath = currentPath;
                if (currentPath.startsWith('/docs')) {
                    setTimeout(checkAndRender, 500);
                }
            }
        }, 300);

        // Watch for content changes in docs-content (tab switches)
        const observer = new MutationObserver(function(mutations) {
            if (!window.location.pathname.startsWith('/docs')) return;

            // Debounce
            clearTimeout(observer.timeout);
            observer.timeout = setTimeout(function() {
                console.log('Content changed, re-rendering mermaid');
                renderMermaidDiagrams();
            }, 400);
        });

        // Start observing when docs-content exists
        function startObserver() {
            const target = document.getElementById('docs-content');
            if (target) {
                observer.observe(target, { childList: true, subtree: true, characterData: true });
                console.log('Mermaid observer started');
            } else {
                setTimeout(startObserver, 500);
            }
        }

        if (window.location.pathname.startsWith('/docs')) {
            setTimeout(startObserver, 1000);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
