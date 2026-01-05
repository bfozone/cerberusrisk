// Mermaid renderer for CerberusRisk documentation
// Uses locally bundled mermaid.min.js (loaded by Dash from assets folder)

(function() {
    'use strict';

    let renderPending = false;

    // Wait for mermaid to be available (loaded from mermaid.min.js)
    function waitForMermaid(callback, attempts) {
        attempts = attempts || 0;
        if (typeof mermaid !== 'undefined') {
            callback();
        } else if (attempts < 50) {
            setTimeout(() => waitForMermaid(callback, attempts + 1), 100);
        } else {
            console.error('Mermaid library not loaded');
        }
    }

    // Get theme config based on current color scheme
    function getThemeConfig() {
        const isDark = document.documentElement.getAttribute('data-mantine-color-scheme') === 'dark';

        return {
            startOnLoad: false,
            theme: isDark ? 'dark' : 'default',
            securityLevel: 'loose',
            themeVariables: isDark ? {
                primaryColor: '#a78bfa',
                primaryTextColor: '#ffffff',
                primaryBorderColor: '#6b5b95',
                lineColor: '#a0a0b0',
                secondaryColor: '#2a2a3a',
                tertiaryColor: '#1a1a24',
                background: '#1a1a24',
                mainBkg: '#2a2a3a',
                nodeBorder: '#a78bfa',
                clusterBkg: '#22222e',
                titleColor: '#e0e0e0',
                edgeLabelBackground: '#2a2a3a',
                textColor: '#e0e0e0',
                nodeTextColor: '#ffffff'
            } : {
                primaryColor: '#7c3aed',
                primaryTextColor: '#1e1b2e',
                primaryBorderColor: '#d8b4fe',
                lineColor: '#4a4760',
                secondaryColor: '#f5f3f7',
                tertiaryColor: '#faf9fb',
                background: '#ffffff',
                mainBkg: '#f8f7fa',
                nodeBorder: '#7c3aed',
                clusterBkg: '#f8f7fa',
                titleColor: '#1e1b2e',
                edgeLabelBackground: '#ffffff'
            }
        };
    }

    // Find and render mermaid diagrams
    async function renderDiagrams() {
        if (renderPending) return;
        if (typeof mermaid === 'undefined') return;

        renderPending = true;

        // Small delay to let DOM settle
        await new Promise(r => setTimeout(r, 150));

        try {
            // Re-initialize mermaid with current theme
            mermaid.initialize(getThemeConfig());

            // Find all pre > code elements
            const codeBlocks = document.querySelectorAll('pre code, pre > code');

            const mermaidKeywords = [
                'flowchart', 'graph', 'sequenceDiagram', 'classDiagram',
                'stateDiagram', 'erDiagram', 'gantt', 'pie', 'journey',
                'gitGraph', 'mindmap', 'timeline', 'quadrantChart', 'xychart'
            ];

            let count = 0;

            for (const code of codeBlocks) {
                const pre = code.parentElement;
                if (!pre || pre.tagName !== 'PRE') continue;
                if (pre.dataset.mermaidDone === 'true') continue;

                const text = code.textContent.trim();
                const firstLine = text.split('\n')[0].trim();

                // Check if it's a mermaid diagram
                const isMermaid = mermaidKeywords.some(kw =>
                    firstLine.startsWith(kw + ' ') ||
                    firstLine.startsWith(kw + '\n') ||
                    firstLine === kw ||
                    firstLine.startsWith(kw + '-')
                );

                if (!isMermaid) continue;

                pre.dataset.mermaidDone = 'true';
                count++;

                // Create unique ID
                const id = 'mermaid-diagram-' + Date.now() + '-' + count;

                // Create container
                const container = document.createElement('div');
                container.className = 'mermaid-container';
                container.style.cssText = 'margin: 1rem 0; overflow-x: auto;';

                const diagramDiv = document.createElement('div');
                diagramDiv.id = id;
                diagramDiv.className = 'mermaid';
                diagramDiv.textContent = text;

                container.appendChild(diagramDiv);

                // Replace pre with container
                pre.parentNode.replaceChild(container, pre);
            }

            if (count > 0) {
                // Run mermaid on new diagrams
                await mermaid.run({
                    querySelector: '.mermaid:not([data-processed="true"])'
                });
            }
        } catch (e) {
            console.error('Mermaid render error:', e);
        } finally {
            renderPending = false;
        }
    }

    // Initialize
    function init() {
        waitForMermaid(() => {
            // Initial render if on docs page
            if (window.location.pathname.includes('/docs')) {
                setTimeout(renderDiagrams, 300);
            }

            // Watch for content changes (Dash callbacks)
            const observer = new MutationObserver((mutations) => {
                if (!window.location.pathname.includes('/docs')) return;

                const hasNewContent = mutations.some(m =>
                    m.addedNodes.length > 0 || m.type === 'characterData'
                );

                if (hasNewContent) {
                    setTimeout(renderDiagrams, 200);
                }
            });

            observer.observe(document.body, {
                childList: true,
                subtree: true,
                characterData: true
            });

            // Watch for theme changes
            const themeObserver = new MutationObserver((mutations) => {
                for (const m of mutations) {
                    if (m.attributeName === 'data-mantine-color-scheme') {
                        // Reset and re-render diagrams with new theme
                        document.querySelectorAll('[data-mermaid-done="true"]').forEach(el => {
                            el.dataset.mermaidDone = 'false';
                        });
                        document.querySelectorAll('.mermaid-container').forEach(el => el.remove());
                        setTimeout(renderDiagrams, 100);
                    }
                }
            });

            themeObserver.observe(document.documentElement, { attributes: true });

            // Handle SPA navigation
            let lastPath = window.location.pathname;
            setInterval(() => {
                if (window.location.pathname !== lastPath) {
                    lastPath = window.location.pathname;
                    if (lastPath.includes('/docs')) {
                        setTimeout(renderDiagrams, 500);
                    }
                }
            }, 200);
        });
    }

    // Start when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
