// Semantic House Search Frontend JavaScript

class SemanticHouseSearch {
    constructor() {
        this.form = document.getElementById('searchForm');
        this.loading = document.getElementById('loading');
        this.results = document.getElementById('results');
        this.error = document.getElementById('error');
        this.noResults = document.getElementById('noResults');
        this.searchBtn = document.getElementById('searchBtn');
        
        this.init();
    }
    
    init() {
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        this.setupExampleQueries();
    }
    
    setupExampleQueries() {
        const queryTextarea = document.getElementById('query');
        const examples = [
            "no one living above me, NOT a fixer-upper",
            "high ceilings, natural light, modern kitchen",
            "quiet neighborhood, outdoor space, parking",
            "move-in ready, city view, not too residential",
            "not edwardian, not super old, safe area like Cole Valley"
        ];
        
        // Add placeholder rotation
        let exampleIndex = 0;
        setInterval(() => {
            if (!queryTextarea.value && document.activeElement !== queryTextarea) {
                queryTextarea.placeholder = examples[exampleIndex];
                exampleIndex = (exampleIndex + 1) % examples.length;
            }
        }, 3000);
    }
    
    async handleSubmit(e) {
        e.preventDefault();
        
        // Hide previous results
        this.hideAllSections();
        
        // Show loading
        this.showLoading();
        
        try {
            // Get form data
            const formData = new FormData(this.form);
            const searchData = {
                query: formData.get('query'),
                min_price: parseInt(formData.get('min_price')),
                max_price: parseInt(formData.get('max_price')),
                min_sqft: parseInt(formData.get('min_sqft')),
                max_sqft: parseInt(formData.get('max_sqft')),
                center: formData.get('center'),
                radius: parseFloat(formData.get('radius'))
            };
            
            // Make API request
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(searchData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.displayResults(data);
            } else {
                this.showError(data.error || 'Search failed');
            }
            
        } catch (error) {
            console.error('Search error:', error);
            this.showError('Network error. Please try again.');
        } finally {
            this.hideLoading();
        }
    }
    
    displayResults(data) {
        this.hideAllSections();
        
        if (!data.properties || data.properties.length === 0) {
            this.showNoResults();
            return;
        }
        
        // Show results section
        this.results.classList.remove('hidden');
        
        // Display summary
        this.displaySummary(data.summary, data.query);
        
        // Display semantic query info
        this.displaySemanticQuery(data.query, data.interpreted_filters);
        
        // Display properties
        this.displayProperties(data.properties);
    }
    
    displaySummary(summary, query) {
        const summaryContainer = document.getElementById('resultsSummary');
        
        summaryContainer.innerHTML = `
            <div class="summary-item">
                <div class="label">Properties Found</div>
                <div class="value">${summary.total_properties}</div>
            </div>
            <div class="summary-item">
                <div class="label">Semantic Matches</div>
                <div class="value">${summary.semantic_matches || 0}</div>
            </div>
            <div class="summary-item">
                <div class="label">Price Range</div>
                <div class="value">$${this.formatNumber(summary.min_price)} - $${this.formatNumber(summary.max_price)}</div>
            </div>
            <div class="summary-item">
                <div class="label">Avg Price</div>
                <div class="value">$${this.formatNumber(summary.avg_price)}</div>
            </div>
        `;
    }
    
    displaySemanticQuery(query, interpretedFilters) {
        const semanticQueryDiv = document.getElementById('semanticQuery');
        const queryTextDiv = document.getElementById('queryText');
        const interpretedFiltersDiv = document.getElementById('interpretedFilters');
        
        if (!query) return;
        
        semanticQueryDiv.classList.remove('hidden');
        queryTextDiv.textContent = `"${query}"`;
        
        // Display interpreted filters
        interpretedFiltersDiv.innerHTML = '';
        
        const filterCategories = [
            { key: 'home_types', label: 'Home Types', color: '#667eea' },
            { key: 'preferences', label: 'Preferences', color: '#28a745' },
            { key: 'exclusions', label: 'Exclusions', color: '#dc3545' },
            { key: 'neighborhood_preferences', label: 'Preferred Areas', color: '#17a2b8' },
            { key: 'neighborhood_exclusions', label: 'Areas to Avoid', color: '#ffc107' }
        ];
        
        filterCategories.forEach(category => {
            const filters = interpretedFilters[category.key];
            if (filters && filters.length > 0) {
                const categoryDiv = document.createElement('div');
                categoryDiv.style.marginBottom = '10px';
                
                const label = document.createElement('strong');
                label.textContent = `${category.label}: `;
                label.style.color = category.color;
                categoryDiv.appendChild(label);
                
                filters.forEach(filter => {
                    const tag = document.createElement('span');
                    tag.className = 'filter-tag';
                    tag.textContent = filter;
                    tag.style.backgroundColor = category.color + '20';
                    tag.style.color = category.color;
                    categoryDiv.appendChild(tag);
                });
                
                interpretedFiltersDiv.appendChild(categoryDiv);
            }
        });
    }
    
    displayProperties(properties) {
        const grid = document.getElementById('propertiesGrid');
        
        grid.innerHTML = properties.map(property => `
            <div class="property-card">
                <img src="${property.image_url || 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="350" height="200" viewBox="0 0 350 200"><rect width="350" height="200" fill="%23f0f0f0"/><text x="175" y="100" font-family="Arial" font-size="16" text-anchor="middle" fill="%23999">No Image</text></svg>'}" 
                     alt="Property photo" class="property-image" 
                     onerror="this.src='data:image/svg+xml,<svg xmlns=\\"http://www.w3.org/2000/svg\\" width=\\"350\\" height=\\"200\\" viewBox=\\"0 0 350 200\\"><rect width=\\"350\\" height=\\"200\\" fill=\\"%23f0f0f0\\"/><text x=\\"175\\" y=\\"100\\" font-family=\\"Arial\\" font-size=\\"16\\" text-anchor=\\"middle\\" fill=\\"%23999\\">No Image</text></svg>'">
                
                <div class="property-content">
                    <div class="property-address">${property.address}</div>
                    
                    <div class="property-price">$${this.formatNumber(property.price)}</div>
                    
                    ${property.semantic_score > 0 ? `<div class="semantic-score">Semantic Score: ${property.semantic_score.toFixed(2)}</div>` : ''}
                    
                    <div class="property-details">
                        <div class="property-detail">
                            <i class="fas fa-bed"></i>
                            ${property.beds || 'N/A'} beds
                        </div>
                        <div class="property-detail">
                            <i class="fas fa-bath"></i>
                            ${property.baths || 'N/A'} baths
                        </div>
                        <div class="property-detail">
                            <i class="fas fa-home"></i>
                            ${this.formatNumber(property.sqft)} sqft
                        </div>
                        <div class="property-detail">
                            <i class="fas fa-tag"></i>
                            $${this.formatNumber(property.price_per_sqft)}/sqft
                        </div>
                    </div>
                    
                    <div class="property-details">
                        <div class="property-detail">
                            <i class="fas fa-building"></i>
                            ${property.home_type}
                        </div>
                        <div class="property-detail">
                            <i class="fas fa-calendar"></i>
                            ${property.year_built || 'Unknown'} built
                        </div>
                    </div>
                    
                    ${property.semantic_matches && property.semantic_matches.length > 0 ? `
                        <div class="semantic-matches">
                            ${property.semantic_matches.map(match => `<span class="semantic-match">${match}</span>`).join('')}
                        </div>
                    ` : ''}
                    
                    <div class="property-actions">
                        <a href="${property.url}" target="_blank" class="view-btn">
                            <i class="fas fa-external-link-alt"></i> View on Zillow
                        </a>
                    </div>
                </div>
            </div>
        `).join('');
    }
    
    showLoading() {
        this.loading.classList.remove('hidden');
        this.searchBtn.disabled = true;
        this.searchBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Searching...';
    }
    
    hideLoading() {
        this.loading.classList.add('hidden');
        this.searchBtn.disabled = false;
        this.searchBtn.innerHTML = '<i class="fas fa-search"></i> Search Properties';
    }
    
    showError(message) {
        this.hideAllSections();
        this.error.classList.remove('hidden');
        document.getElementById('errorMessage').textContent = message;
    }
    
    showNoResults() {
        this.hideAllSections();
        this.noResults.classList.remove('hidden');
    }
    
    hideAllSections() {
        this.results.classList.add('hidden');
        this.error.classList.add('hidden');
        this.noResults.classList.add('hidden');
    }
    
    formatNumber(num) {
        if (!num) return 'N/A';
        return new Intl.NumberFormat().format(Math.round(num));
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new SemanticHouseSearch();
});

// Add some helpful keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + Enter to submit form
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        const form = document.getElementById('searchForm');
        if (form) {
            form.dispatchEvent(new Event('submit'));
        }
    }
});
