// ORXL Documentation Site - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add active state to nav links based on scroll position
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('.nav-links a[href^="#"]');

    function highlightNavigation() {
        const scrollY = window.pageYOffset;

        sections.forEach(section => {
            const sectionHeight = section.offsetHeight;
            const sectionTop = section.offsetTop - 100;
            const sectionId = section.getAttribute('id');

            if (scrollY > sectionTop && scrollY <= sectionTop + sectionHeight) {
                navLinks.forEach(link => {
                    link.classList.remove('active');
                    if (link.getAttribute('href') === `#${sectionId}`) {
                        link.classList.add('active');
                    }
                });
            }
        });
    }

    window.addEventListener('scroll', highlightNavigation);

    // Animate stats on scroll
    const stats = document.querySelectorAll('.stat-value');
    const observerOptions = {
        threshold: 0.5,
        rootMargin: '0px 0px -100px 0px'
    };

    const statsObserver = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animated');
                statsObserver.unobserve(entry.target);
            }
        });
    }, observerOptions);

    stats.forEach(stat => {
        statsObserver.observe(stat);
    });

    // Animate feature cards on scroll
    const featureCards = document.querySelectorAll('.feature-card, .domain-card');
    
    const cardsObserver = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '0';
                entry.target.style.transform = 'translateY(20px)';
                
                setTimeout(() => {
                    entry.target.style.transition = 'all 0.6s ease';
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }, 100);
                
                cardsObserver.unobserve(entry.target);
            }
        });
    }, observerOptions);

    featureCards.forEach(card => {
        cardsObserver.observe(card);
    });

    // Code window syntax highlighting (already done in CSS, but could add more here)
    
    // Add copy button to code snippets
    document.querySelectorAll('.code-snippet code, .code-content code').forEach(codeBlock => {
        const wrapper = codeBlock.parentElement;
        if (!wrapper.querySelector('.copy-btn')) {
            const copyBtn = document.createElement('button');
            copyBtn.className = 'copy-btn';
            copyBtn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path d="M5.75 4.75H10.25M5.75 7.75H10.25M5.75 10.75H8.25M12.25 1.75H3.75C2.92157 1.75 2.25 2.42157 2.25 3.25V12.75C2.25 13.5784 2.92157 14.25 3.75 14.25H12.25C13.0784 14.25 13.75 13.5784 13.75 12.75V3.25C13.75 2.42157 13.0784 1.75 12.25 1.75Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            `;
            copyBtn.title = 'Copy code';
            
            copyBtn.addEventListener('click', function() {
                const code = codeBlock.textContent;
                navigator.clipboard.writeText(code).then(() => {
                    copyBtn.innerHTML = `
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                            <path d="M13.25 4.75L6 12L2.75 8.75" stroke="#4ade80" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    `;
                    setTimeout(() => {
                        copyBtn.innerHTML = `
                            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                                <path d="M5.75 4.75H10.25M5.75 7.75H10.25M5.75 10.75H8.25M12.25 1.75H3.75C2.92157 1.75 2.25 2.42157 2.25 3.25V12.75C2.25 13.5784 2.92157 14.25 3.75 14.25H12.25C13.0784 14.25 13.75 13.5784 13.75 12.75V3.25C13.75 2.42157 13.0784 1.75 12.25 1.75Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                        `;
                    }, 2000);
                });
            });
            
            wrapper.style.position = 'relative';
            wrapper.appendChild(copyBtn);
        }
    });
});

// Add CSS for copy button
const style = document.createElement('style');
style.textContent = `
    .copy-btn {
        position: absolute;
        top: 0.75rem;
        right: 0.75rem;
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        color: var(--text-secondary);
        padding: 0.5rem;
        border-radius: 0.375rem;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s ease;
        opacity: 0;
    }
    
    .code-snippet:hover .copy-btn,
    .code-content:hover .copy-btn {
        opacity: 1;
    }
    
    .copy-btn:hover {
        background: var(--bg-tertiary);
        border-color: var(--accent-color);
        color: var(--accent-color);
    }
`;
document.head.appendChild(style);
