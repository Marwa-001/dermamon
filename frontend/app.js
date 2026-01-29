// Product Analysis
async function analyzeProduct(e) {
    e.preventDefault();
    document.getElementById('loading').classList.add('active');
    document.getElementById('productAnalysisForm').style.display = 'none';

    try {
        const res = await fetch(`${API_URL}/predict`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                product: document.getElementById('productInput').value,
                skin_type: document.getElementById('skinType').value,
                allergies: document.getElementById('allergies').value
            })
        });
        const data = await res.json();
        displayResults(data);
    } catch (err) {
        showError('Analysis failed. Check if backend is running.');
        document.getElementById('loading').classList.remove('active');
        document.getElementById('productAnalysisForm').style.display = 'block';
    }
}

function displayResults(data) {
    document.getElementById('loading').classList.remove('active');
    const results = document.getElementById('results');
    results.classList.add('active');
    results.className = 'results active ' + (data.prediction.safe ? 'result-safe' : 'result-unsafe');
    
    document.getElementById('resultIcon').textContent = data.prediction.safe ? '✅' : '⚠️';
    document.getElementById('resultTitle').textContent = data.product_name || 'Analysis Complete';
    document.getElementById('resultSubtitle').textContent = `${data.prediction.risk_category} Risk`;
    
    setTimeout(() => {
        document.getElementById('confidenceFill').style.width = data.prediction.confidence + '%';
    }, 100);
    
    document.getElementById('confidenceText').textContent = 
        `Confidence: ${data.prediction.confidence.toFixed(1)}% | Risk: ${data.prediction.risk_score}/100`;
    
    let details = `<h3>📊 Analysis</h3>`;
    details += `<p><strong>Ingredients:</strong> ${data.analysis.total_ingredients}</p>`;
    details += `<p><strong>Beneficial:</strong> ${data.analysis.beneficial_ingredients.join(', ') || 'None'}</p>`;
    
    if (data.analysis.high_risk_ingredients.length > 0) {
        details += `<p style="color: var(--danger);"><strong>⚠️ High Risk:</strong> ${data.analysis.high_risk_ingredients.join(', ')}</p>`;
    }
    
    if (data.product_details) {
        details += `<h3>ℹ️ Product Info</h3>`;
        details += `<p><strong>Brand:</strong> ${data.product_details.brand}</p>`;
        details += `<p><strong>Category:</strong> ${data.product_details.category}</p>`;
        details += `<p><strong>Suitable for:</strong> ${data.product_details.suitable_for.join(', ')}</p>`;
    }
    
    details += `<h3>💡 Recommendations</h3><ul>`;
    data.recommendations.forEach(r => details += `<li>${r}</li>`);
    details += `</ul>`;
    
    document.getElementById('resultDetails').innerHTML = details;
}

// Recommendations
async function getRecommendations(e) {
    e.preventDefault();
    document.getElementById('loading').classList.add('active');
    document.getElementById('recommendationForm').style.display = 'none';

    try {
        const res = await fetch(`${API_URL}/recommend`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                skin_type: document.getElementById('recSkinType').value,
                concern: document.getElementById('skinConcern').value,
                product_type: document.getElementById('productType').value
            })
        });
        const data = await res.json();
        
        document.getElementById('loading').classList.remove('active');
        const results = document.getElementById('results');
        results.classList.add('active');
        results.className = 'results active result-safe';
        
        document.getElementById('resultIcon').textContent = '✨';
        document.getElementById('resultTitle').textContent = 'Recommendations';
        document.getElementById('resultSubtitle').textContent = `For ${data.skin_type} skin`;
        document.getElementById('confidenceFill').style.width = '0%';
        document.getElementById('confidenceText').textContent = '';
        
        let details = '<div>';
        data.recommendations.forEach((p, i) => {
            details += `<div style="background: var(--bg-light); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                <h4>${i + 1}. ${p}</h4></div>`;
        });
        details += `</div><h3>🌟 Look for:</h3><p>${data.beneficial_ingredients.join(', ')}</p>`;
        document.getElementById('resultDetails').innerHTML = details;
    } catch (err) {
        showError('Failed to get recommendations');
        document.getElementById('loading').classList.remove('active');
        document.getElementById('recommendationForm').style.display = 'block';
    }
}

async function analyzeAllergy(e) {
    e.preventDefault();
    
    const symptomsField = document.getElementById('allergySymptoms');
    const imageFile = document.getElementById('allergyImage').files[0];
    
    // Validate: either symptoms or image must be provided
    if (!symptomsField.value.trim() && !imageFile) {
        showError('Please either describe symptoms or upload an image');
        return;
    }
    
    document.getElementById('loading').classList.add('active');
    document.getElementById('allergyCheckForm').classList.remove('active'); // Changed from style.display

    let imageBase64 = null;

    if (imageFile) {
        imageBase64 = await new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result.split(',')[1]);
            reader.readAsDataURL(imageFile);
        });
    }

    try {
        const res = await fetch(`${API_URL}/allergy/analyze`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                symptoms: symptomsField.value,
                suspected_ingredients: document.getElementById('suspectedIngredients').value,
                image: imageBase64
            })
        });
        const data = await res.json();
        
        document.getElementById('loading').classList.remove('active');
        const results = document.getElementById('results');
        results.classList.add('active');
        results.className = 'results active result-unsafe';
        
        document.getElementById('resultIcon').textContent = '🩺';
        document.getElementById('resultTitle').textContent = 'Allergy Analysis';
        document.getElementById('resultSubtitle').textContent = 'AI-Powered Detection';
        document.getElementById('confidenceFill').style.width = '0%';
        document.getElementById('confidenceText').textContent = '';
        
        let details = `<h3>🔍 Likely Culprits</h3>`;
        details += `<p>${data.likely_culprits.join(', ')}</p>`;
        
        if (data.image_analysis) {
            details += `<h3>📸 Image Analysis</h3>`;
            details += `<p><strong>Severity:</strong> ${data.image_analysis.severity}</p>`;
            details += `<p><strong>Type:</strong> ${data.image_analysis.type}</p>`;
            details += `<p><strong>Confidence:</strong> ${data.image_analysis.confidence}%</p>`;
            if (data.image_analysis.observations) {
                details += `<p><strong>Observations:</strong></p><ul>`;
                data.image_analysis.observations.forEach(o => details += `<li>${o}</li>`);
                details += `</ul>`;
            }
        }
        
        details += `<h3>💊 Remedies</h3>`;
        data.remedies.forEach(r => {
            details += `<p><strong>${r.ingredient}:</strong> ${r.remedy}</p>`;
        });
        details += `<h3>📋 General Advice</h3><ul>`;
        data.general_advice.forEach(a => details += `<li>${a}</li>`);
        details += `</ul>`;
        
        document.getElementById('resultDetails').innerHTML = details;
    } catch (err) {
        showError('Allergy analysis failed. Please try again.');
        document.getElementById('loading').classList.remove('active');
        document.getElementById('allergyCheckForm').classList.add('active');
    }
}

function previewAllergyImage(event) {
    const file = event.target.files[0];
    const preview = document.getElementById('imagePreview');
    const symptomsField = document.getElementById('allergySymptoms');
    const symptomsRequired = document.getElementById('symptomsRequired');
    const symptomsHint = document.getElementById('symptomsHint');
    
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.innerHTML = `<img src="${e.target.result}" style="max-width: 300px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">`;
            
            // Make symptoms optional when image is uploaded
            symptomsField.removeAttribute('required');
            symptomsRequired.textContent = '(Optional)';
            symptomsHint.textContent = 'Image uploaded - symptoms are optional but help improve accuracy';
        }
        reader.readAsDataURL(file);
    } else {
        preview.innerHTML = '';
        // Make symptoms required again if no image
        symptomsField.setAttribute('required', 'required');
        symptomsRequired.textContent = '(Required)';
        symptomsHint.textContent = 'Describe your symptoms in detail';
    }
}

// Reviews/Feedback
async function submitReview(e) {
    e.preventDefault();
    
    const name = document.getElementById('reviewName').value;
    const email = document.getElementById('reviewEmail').value;
    const rating = document.getElementById('reviewRating').value;
    const feedback = document.getElementById('reviewText').value;
    
    try {
        // For now, just show success message
        // You can add API call here if you want to save to database
        showSuccess(`Thank you ${name}! Your feedback has been submitted.`);
        
        // Reset form
        document.getElementById('reviewName').value = '';
        document.getElementById('reviewEmail').value = '';
        document.getElementById('reviewRating').value = '';
        document.getElementById('reviewText').value = '';
        
        closeForm('reviewsSection');
    } catch (err) {
        showError('Failed to submit feedback. Please try again.');
    }
}

function previewImage(event) {
    const file = event.target.files[0];
    const preview = document.getElementById('imagePreview');
    
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.innerHTML = `<img src="${e.target.result}" style="max-width: 300px; border-radius: 8px;">`;
        }
        reader.readAsDataURL(file);
    }
}

// async function analyzeAllergy(e) {
//     e.preventDefault();
//     document.getElementById('loading').classList.add('active');
//     document.getElementById('allergyCheckForm').style.display = 'none';

//     const imageFile = document.getElementById('allergyImage').files[0];
//     let imageBase64 = null;

//     if (imageFile) {
//         imageBase64 = await new Promise((resolve) => {
//             const reader = new FileReader();
//             reader.onload = () => resolve(reader.result.split(',')[1]);
//             reader.readAsDataURL(imageFile);
//         });
//     }

//     try {
//         const res = await fetch(`${API_URL}/allergy/analyze`, {
//             method: 'POST',
//             headers: {'Content-Type': 'application/json'},
//             body: JSON.stringify({
//                 symptoms: document.getElementById('allergySymptoms').value,
//                 suspected_ingredients: document.getElementById('suspectedIngredients').value,
//                 image: imageBase64  // Send base64 image
//             })
//         });
//         const data = await res.json();
        
//         // ... rest of your code
//     } catch (err) {
//         showError('Allergy analysis failed');
//     }
// }