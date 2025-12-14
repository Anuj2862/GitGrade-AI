/**
 * GitGrade Frontend Application
 * Handles UI interactions, API calls, and visualizations
 */

// Configuration
const API_URL = 'http://localhost:8001/api'; // Updated to 8001 for stability

// State
let currentTaskId = null;
let pollingInterval = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('analyzeForm').addEventListener('submit', handleSubmit);
});

// Form submission
async function handleSubmit(e) {
    e.preventDefault();

    const repoUrl = document.getElementById('repoUrl').value.trim();

    if (!isValidGitHubUrl(repoUrl)) {
        showError('Invalid URL', 'Please enter a valid GitHub repository URL (https://github.com/username/repository)');
        return;
    }

    await analyzeRepository(repoUrl);
}

// Main analysis function
async function analyzeRepository(repoUrl) {
    try {
        showLoading();
        updateProgress(0, 'Starting analysis...');

        const response = await fetch(`${API_URL}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ repo_url: repoUrl })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Analysis failed');
        }

        const data = await response.json();
        currentTaskId = data.task_id;

        // Check if cached (instant result)
        if (data.cached) {
            updateProgress(100, 'Analysis complete (cached)');
            setTimeout(async () => {
                const progress = await getProgress(currentTaskId);
                if (progress.result) {
                    displayResults(progress.result);
                }
            }, 500);
        } else {
            // Start polling
            startPolling();
        }

    } catch (error) {
        console.error('Analysis error:', error);
        handleError(error);
    }
}

// Polling for progress
function startPolling() {
    updateProgress(10, 'Fetching repository data...');

    pollingInterval = setInterval(async () => {
        try {
            const progress = await getProgress(currentTaskId);

            updateProgress(progress.progress, progress.message);

            if (progress.status === 'completed') {
                clearInterval(pollingInterval);
                displayResults(progress.result);
            } else if (progress.status === 'failed') {
                clearInterval(pollingInterval);
                throw new Error(progress.error || 'Analysis failed');
            }
        } catch (error) {
            clearInterval(pollingInterval);
            handleError(error);
        }
    }, 2000); // Poll every 2 seconds
}

// Get progress
async function getProgress(taskId) {
    const response = await fetch(`${API_URL}/progress/${taskId}`);
    if (!response.ok) {
        throw new Error('Failed to get progress');
    }
    return await response.json();
}

// Display results
function displayResults(result) {
    hideLoading();
    showResults();

    // Set repo name
    document.getElementById('repoName').textContent = result.repo_name;

    // Animate score
    animateScore(result.total_score);

    // Update skill level and percentile
    document.getElementById('skillLevel').textContent = result.skill_level;
    document.getElementById('percentile').textContent =
        `Better than ${result.percentile}% of analyzed repositories`;

    // Create radar chart
    createRadarChart(result.dimensions);

    // Display dimension cards
    displayDimensions(result.dimensions);

    // Display AI insights
    document.getElementById('aiSummary').textContent = result.ai_insights.summary;

    // Display roadmap
    displayRoadmap(result.ai_insights.roadmap);
}

// Animate score with GSAP
function animateScore(targetScore) {
    const scoreElement = document.getElementById('totalScore');

    gsap.to({ value: 0 }, {
        value: targetScore,
        duration: 2,
        ease: 'power2.out',
        onUpdate: function () {
            scoreElement.textContent = Math.round(this.targets()[0].value);
        }
    });
}

// Create radar chart with Chart.js
function createRadarChart(dimensions) {
    const ctx = document.getElementById('radarChart').getContext('2d');

    const labels = Object.keys(dimensions).map(key =>
        formatDimensionName(key)
    );

    const scores = Object.values(dimensions).map(dim =>
        (dim.score / dim.max_score) * 100
    );

    new Chart(ctx, {
        type: 'radar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Score',
                data: scores,
                backgroundColor: 'rgba(139, 92, 246, 0.2)',
                borderColor: 'rgba(139, 92, 246, 1)',
                borderWidth: 2,
                pointBackgroundColor: 'rgba(139, 92, 246, 1)',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: 'rgba(139, 92, 246, 1)',
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        stepSize: 20,
                        color: '#94A3B8'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    angleLines: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    pointLabels: {
                        color: '#CBD5E1',
                        font: {
                            size: 12
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

// Display dimension cards
function displayDimensions(dimensions) {
    const container = document.getElementById('dimensionCards');
    container.innerHTML = '';

    Object.entries(dimensions).forEach(([key, dim]) => {
        const card = document.createElement('div');
        card.className = 'dimension-card';

        const percentage = Math.round((dim.score / dim.max_score) * 100);

        card.innerHTML = `
            <h3>${formatDimensionName(key)}</h3>
            <div class="dimension-score">${dim.score} / ${dim.max_score} <span style="font-size: 1rem; color: var(--text-muted);">(${percentage}%)</span></div>
            <div class="dimension-signals">
                ${dim.signals.map(signal => `<div class="signal">${signal}</div>`).join('')}
            </div>
            <div class="dimension-formula">${dim.formula}</div>
        `;

        container.appendChild(card);

        // Animate card entrance
        gsap.from(card, {
            opacity: 0,
            y: 20,
            duration: 0.5,
            delay: Object.keys(dimensions).indexOf(key) * 0.1
        });
    });
}

// Display roadmap
function displayRoadmap(roadmap) {
    const container = document.getElementById('roadmapList');
    container.innerHTML = '';

    roadmap.forEach((item, index) => {
        const roadmapItem = document.createElement('div');
        roadmapItem.className = 'roadmap-item';
        roadmapItem.innerHTML = `
            <div class="roadmap-number">${index + 1}</div>
            <div class="roadmap-content">
                <h4>${item.item}</h4>
                <p>${item.reason}</p>
            </div>
        `;
        container.appendChild(roadmapItem);

        // Animate roadmap items
        gsap.from(roadmapItem, {
            opacity: 0,
            x: -20,
            duration: 0.5,
            delay: index * 0.15
        });
    });
}

// UI State Management
function showLoading() {
    document.getElementById('hero').classList.add('hidden');
    document.getElementById('loading').classList.remove('hidden');
    document.getElementById('results').classList.add('hidden');
    document.getElementById('error').classList.add('hidden');
}

function hideLoading() {
    document.getElementById('loading').classList.add('hidden');
}

function showResults() {
    document.getElementById('results').classList.remove('hidden');

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showError(title, message) {
    document.getElementById('hero').classList.add('hidden');
    document.getElementById('loading').classList.add('hidden');
    document.getElementById('error').classList.remove('hidden');

    document.getElementById('errorTitle').textContent = title;
    document.getElementById('errorMessage').textContent = message;
}

function updateProgress(percent, message) {
    document.getElementById('progressFill').style.width = `${percent}%`;
    document.getElementById('progressPercent').textContent = `${percent}%`;
    document.getElementById('loadingText').textContent = message;
}

// Error handling
function handleError(error) {
    let title = 'Analysis Failed';
    let message = error.message;

    // User-friendly error messages
    if (message.includes('404') || message.includes('not found')) {
        title = 'Repository Not Found';
        message = 'This repository doesn\'t exist or is private. Please check the URL and try again.';
    } else if (message.includes('429') || message.includes('rate limit')) {
        title = 'Rate Limit Exceeded';
        message = 'Too many requests. Please try again in a few minutes.';
    } else if (message.includes('timeout')) {
        title = 'Request Timeout';
        message = 'The analysis took too long. Please try a smaller repository.';
    } else if (message.includes('Offline mode')) {
        title = 'Offline Mode';
        message = 'Only cached repositories are available. ' + message;
    }

    showError(title, message);
}

// Utility functions
function isValidGitHubUrl(url) {
    const pattern = /^https:\/\/github\.com\/[\w-]+\/[\w.-]+\/?$/;
    return pattern.test(url);
}

function formatDimensionName(key) {
    return key
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}
