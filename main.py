"""
Flask Industrial Control System Dashboard
Complete application with database, API, and real-time control

Installation:
pip install flask flask-cors

Run:
python app.py

Then open: http://localhost:5000
"""

from flask import Flask, render_template_string, jsonify, request
from flask_cors import CORS
from datetime import datetime
import json
import threading
import time
import random

app = Flask(__name__)
CORS(app)

# In-memory storage (replace with database in production)
outputs = []
inputs = []
sensor_values = {'temperature': 22.0, 'humidity': 45.0}

# Initialize outputs
for i in range(1, 7):
    outputs.append({
        'id': i,
        'name': f'Output {i}',
        'status': False,
        'mode': 'manual',
        'manualOverride': False,
        'periodicConfig': {'onDuration': 60, 'offDuration': 60},
        'scheduledPrograms': [],
        'sensorConfig': {'type': 'temperature', 'threshold': 25, 'action': 'on'},
        'lastToggle': time.time()
    })

# Initialize inputs
for i in range(1, 7):
    inputs.append({
        'id': i,
        'name': f'Input {i}',
        'status': random.choice([True, False])
    })

def control_logic():
    """Background thread to handle automatic control logic"""
    while True:
        global outputs, sensor_values
        current_time = datetime.now()
        current_time_str = current_time.strftime('%H:%M')
        
        for output in outputs:
            if output['manualOverride']:
                continue
                
            if output['mode'] == 'periodic':
                config = output['periodicConfig']
                cycle_time = config['onDuration'] + config['offDuration']
                elapsed = time.time() - output['lastToggle']
                in_on_phase = (elapsed % cycle_time) < config['onDuration']
                output['status'] = in_on_phase
                
            elif output['mode'] == 'scheduled':
                should_be_on = False
                for program in output['scheduledPrograms']:
                    if program['onTime'] <= current_time_str < program['offTime']:
                        should_be_on = True
                        break
                output['status'] = should_be_on
                
            elif output['mode'] == 'sensor':
                config = output['sensorConfig']
                sensor_value = sensor_values[config['type']]
                threshold_met = sensor_value < config['threshold']
                output['status'] = threshold_met if config['action'] == 'on' else not threshold_met
        
        time.sleep(1)

def sensor_simulator():
    """Simulate sensor value changes"""
    global sensor_values
    while True:
        sensor_values['temperature'] = max(15, min(35, 
            sensor_values['temperature'] + (random.random() - 0.5) * 2))
        sensor_values['humidity'] = max(20, min(80, 
            sensor_values['humidity'] + (random.random() - 0.5) * 5))
        time.sleep(3)

# Start background threads
threading.Thread(target=control_logic, daemon=True).start()
threading.Thread(target=sensor_simulator, daemon=True).start()

# API Routes
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/outputs', methods=['GET'])
def get_outputs():
    return jsonify(outputs)

@app.route('/api/outputs/<int:output_id>', methods=['PUT'])
def update_output(output_id):
    data = request.json
    for output in outputs:
        if output['id'] == output_id:
            output.update(data)
            if 'mode' in data:
                output['lastToggle'] = time.time()
            return jsonify(output)
    return jsonify({'error': 'Output not found'}), 404

@app.route('/api/outputs/<int:output_id>/toggle', methods=['POST'])
def toggle_output(output_id):
    for output in outputs:
        if output['id'] == output_id:
            output['status'] = not output['status']
            output['manualOverride'] = True
            output['mode'] = 'manual'
            return jsonify(output)
    return jsonify({'error': 'Output not found'}), 404

@app.route('/api/outputs/<int:output_id>/override', methods=['POST'])
def toggle_override(output_id):
    for output in outputs:
        if output['id'] == output_id:
            output['manualOverride'] = not output['manualOverride']
            return jsonify(output)
    return jsonify({'error': 'Output not found'}), 404

@app.route('/api/inputs', methods=['GET'])
def get_inputs():
    return jsonify(inputs)

@app.route('/api/inputs/<int:input_id>', methods=['PUT'])
def update_input(input_id):
    data = request.json
    for inp in inputs:
        if inp['id'] == input_id:
            inp.update(data)
            return jsonify(inp)
    return jsonify({'error': 'Input not found'}), 404

@app.route('/api/sensors', methods=['GET'])
def get_sensors():
    return jsonify(sensor_values)

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({
        'outputs': outputs,
        'inputs': inputs,
        'sensors': sensor_values,
        'timestamp': datetime.now().isoformat()
    })

# HTML Template with embedded CSS and JavaScript
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Industrial Control Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0f;
            color: #fff;
            padding: 1rem;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            flex-wrap: wrap;
            gap: 1rem;
        }
        
        .header h1 {
            font-size: 2rem;
        }
        
        .time-display {
            text-align: right;
        }
        
        .time {
            font-size: 1.5rem;
            font-family: monospace;
        }
        
        .date {
            font-size: 0.875rem;
            color: #9ca3af;
        }
        
        .card {
            background: #1f2937;
            border: 1px solid #374151;
            border-radius: 0.5rem;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }
        
        .sensors {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
        }
        
        .sensor-item {
            background: #111827;
            padding: 1.5rem;
            border-radius: 0.5rem;
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .sensor-icon {
            width: 3rem;
            height: 3rem;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2rem;
        }
        
        .sensor-value {
            font-size: 1.5rem;
            font-weight: bold;
        }
        
        .sensor-label {
            font-size: 0.875rem;
            color: #9ca3af;
        }
        
        .section-title {
            font-size: 1.25rem;
            margin-bottom: 1rem;
            font-weight: 600;
        }
        
        .outputs-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1rem;
        }
        
        .output-card {
            background: #1f2937;
            border: 1px solid #374151;
            border-radius: 0.5rem;
            padding: 1rem;
        }
        
        .output-header {
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 1rem;
        }
        
        .output-info h3 {
            font-size: 1.125rem;
            margin-bottom: 0.25rem;
        }
        
        .output-mode {
            font-size: 0.875rem;
            color: #9ca3af;
            display: flex;
            align-items: center;
            gap: 0.25rem;
        }
        
        .status-indicator {
            width: 4rem;
            height: 4rem;
            border-radius: 0.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2rem;
            transition: background-color 0.3s;
        }
        
        .status-on {
            background: #10b981;
        }
        
        .status-off {
            background: #374151;
        }
        
        .mode-display {
            background: #111827;
            padding: 0.5rem;
            border-radius: 0.25rem;
            font-size: 0.75rem;
            color: #9ca3af;
            margin-bottom: 0.75rem;
        }
        
        .controls {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.5rem;
            margin-bottom: 0.5rem;
        }
        
        .controls.full {
            grid-template-columns: 1fr;
        }
        
        select, button, input {
            padding: 0.5rem;
            border-radius: 0.25rem;
            border: 1px solid #374151;
            background: #374151;
            color: #fff;
            font-size: 0.875rem;
            cursor: pointer;
            transition: background 0.2s;
        }
        
        button:hover {
            background: #4b5563;
        }
        
        button.primary {
            background: #3b82f6;
        }
        
        button.primary:hover {
            background: #2563eb;
        }
        
        button.success {
            background: #10b981;
        }
        
        button.success:hover {
            background: #059669;
        }
        
        button.danger {
            background: #ef4444;
        }
        
        button.danger:hover {
            background: #dc2626;
        }
        
        .inputs-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 1rem;
        }
        
        .input-card {
            background: #1f2937;
            border: 1px solid #374151;
            border-radius: 0.5rem;
            padding: 1rem;
            text-align: center;
        }
        
        .input-card input {
            width: 100%;
            text-align: center;
            margin-bottom: 0.75rem;
        }
        
        .input-status {
            width: 3rem;
            height: 3rem;
            border-radius: 50%;
            margin: 0.75rem auto;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
        }
        
        .input-label {
            font-size: 0.75rem;
            color: #9ca3af;
        }
        
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.8);
            z-index: 1000;
            align-items: center;
            justify-content: center;
            padding: 1rem;
        }
        
        .modal.active {
            display: flex;
        }
        
        .modal-content {
            background: #1f2937;
            border: 1px solid #374151;
            border-radius: 0.5rem;
            padding: 1.5rem;
            max-width: 500px;
            width: 100%;
            max-height: 90vh;
            overflow-y: auto;
        }
        
        .modal-header {
            font-size: 1.25rem;
            margin-bottom: 1rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid #374151;
        }
        
        .form-group {
            margin-bottom: 1rem;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-size: 0.875rem;
            color: #9ca3af;
        }
        
        .form-group input,
        .form-group select {
            width: 100%;
        }
        
        .program-list {
            max-height: 200px;
            overflow-y: auto;
            margin-top: 1rem;
        }
        
        .program-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #111827;
            padding: 0.5rem;
            border-radius: 0.25rem;
            margin-bottom: 0.5rem;
        }
        
        .program-item button {
            padding: 0.25rem 0.5rem;
            font-size: 0.75rem;
        }
        
        @media (max-width: 768px) {
            .outputs-grid {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 1.5rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏭 Control Dashboard</h1>
            <div class="time-display">
                <div class="time" id="current-time">--:--:--</div>
                <div class="date" id="current-date">---</div>
            </div>
        </div>
        
        <div class="card">
            <div class="sensors">
                <div class="sensor-item">
                    <div class="sensor-icon">🌡️</div>
                    <div>
                        <div class="sensor-label">Temperature</div>
                        <div class="sensor-value" id="temp-value">--°C</div>
                    </div>
                </div>
                <div class="sensor-item">
                    <div class="sensor-icon">💧</div>
                    <div>
                        <div class="sensor-label">Humidity</div>
                        <div class="sensor-value" id="humidity-value">--%</div>
                    </div>
                </div>
            </div>
        </div>
        
        <h2 class="section-title">Outputs</h2>
        <div class="outputs-grid" id="outputs-container"></div>
        
        <h2 class="section-title">Inputs</h2>
        <div class="inputs-grid" id="inputs-container"></div>
    </div>
    
    <div class="modal" id="config-modal">
        <div class="modal-content">
            <div class="modal-header" id="modal-title">Configuration</div>
            <div id="modal-body"></div>
        </div>
    </div>
    
    <script>
        let currentOutput = null;
        let currentMode = null;
        
        function updateTime() {
            const now = new Date();
            document.getElementById('current-time').textContent = now.toLocaleTimeString();
            document.getElementById('current-date').textContent = now.toLocaleDateString();
        }
        
        async function fetchStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                updateOutputs(data.outputs);
                updateInputs(data.inputs);
                updateSensors(data.sensors);
            } catch (error) {
                console.error('Error fetching status:', error);
            }
        }
        
        function updateSensors(sensors) {
            document.getElementById('temp-value').textContent = sensors.temperature.toFixed(1) + '°C';
            document.getElementById('humidity-value').textContent = sensors.humidity.toFixed(0) + '%';
        }
        
        function updateOutputs(outputs) {
            const container = document.getElementById('outputs-container');
            container.innerHTML = outputs.map(output => `
                <div class="output-card">
                    <div class="output-header">
                        <div class="output-info">
                            <h3>${output.name}</h3>
                            <div class="output-mode">
                                ${getModeIcon(output.mode)} ${output.mode.toUpperCase()}
                                ${output.manualOverride ? ' 🔓 OVERRIDE' : ''}
                            </div>
                        </div>
                        <div class="status-indicator ${output.status ? 'status-on' : 'status-off'}">
                            ${output.status ? '▶️' : '⏸️'}
                        </div>
                    </div>
                    
                    <div class="mode-display">${getModeDisplay(output)}</div>
                    
                    <div class="controls ${output.mode === 'manual' ? '' : ''}">
                        <select onchange="changeMode(${output.id}, this.value)">
                            <option value="manual" ${output.mode === 'manual' ? 'selected' : ''}>Manual</option>
                            <option value="periodic" ${output.mode === 'periodic' ? 'selected' : ''}>Periodic</option>
                            <option value="scheduled" ${output.mode === 'scheduled' ? 'selected' : ''}>Scheduled</option>
                            <option value="sensor" ${output.mode === 'sensor' ? 'selected' : ''}>Sensor</option>
                        </select>
                        
                        ${output.mode !== 'manual' ? 
                            `<button onclick="openConfig(${output.id}, '${output.mode}')" class="primary">⚙️ Config</button>` :
                            `<button onclick="toggleOutput(${output.id})" class="${output.status ? 'danger' : 'success'}">
                                ${output.status ? 'Turn OFF' : 'Turn ON'}
                            </button>`
                        }
                    </div>
                    
                    ${output.mode !== 'manual' ? `
                        <button onclick="toggleOverride(${output.id})" 
                                class="${output.manualOverride ? 'danger' : 'primary'}" 
                                style="width: 100%; margin-top: 0.5rem;">
                            ${output.manualOverride ? '🔓 Release Override' : '🔒 Enable Override'}
                        </button>
                        
                        ${output.manualOverride ? `
                            <div class="controls" style="margin-top: 0.5rem;">
                                <button onclick="forceOutput(${output.id}, true)" class="success">Force ON</button>
                                <button onclick="forceOutput(${output.id}, false)" class="danger">Force OFF</button>
                            </div>
                        ` : ''}
                    ` : ''}
                </div>
            `).join('');
        }
        
        function updateInputs(inputs) {
            const container = document.getElementById('inputs-container');
            container.innerHTML = inputs.map(input => `
                <div class="input-card">
                    <input type="text" value="${input.name}" 
                           onchange="updateInputName(${input.id}, this.value)">
                    <div class="input-status ${input.status ? 'status-on' : 'status-off'}">
                        ⚡
                    </div>
                    <div class="input-label">${input.status ? 'ACTIVE' : 'INACTIVE'}</div>
                </div>
            `).join('');
        }
        
        function getModeIcon(mode) {
            const icons = {
                manual: '🎮',
                periodic: '🔄',
                scheduled: '⏰',
                sensor: '📊'
            };
            return icons[mode] || '';
        }
        
        function getModeDisplay(output) {
            switch(output.mode) {
                case 'periodic':
                    return `${output.periodicConfig.onDuration}s ON / ${output.periodicConfig.offDuration}s OFF`;
                case 'scheduled':
                    return `${output.scheduledPrograms.length} programs active`;
                case 'sensor':
                    return `${output.sensorConfig.type}: ${output.sensorConfig.action === 'on' ? '<' : '>'} ${output.sensorConfig.threshold}`;
                default:
                    return 'Manual Control';
            }
        }
        
        async function changeMode(outputId, mode) {
            const response = await fetch(`/api/outputs/${outputId}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({mode, manualOverride: false})
            });
            if (response.ok) fetchStatus();
        }
        
        async function toggleOutput(outputId) {
            await fetch(`/api/outputs/${outputId}/toggle`, {method: 'POST'});
            fetchStatus();
        }
        
        async function toggleOverride(outputId) {
            await fetch(`/api/outputs/${outputId}/override`, {method: 'POST'});
            fetchStatus();
        }
        
        async function forceOutput(outputId, status) {
            await fetch(`/api/outputs/${outputId}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({status})
            });
            fetchStatus();
        }
        
        async function updateInputName(inputId, name) {
            await fetch(`/api/inputs/${inputId}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name})
            });
        }
        
        async function openConfig(outputId, mode) {
            const response = await fetch('/api/outputs');
            const outputs = await response.json();
            currentOutput = outputs.find(o => o.id === outputId);
            currentMode = mode;
            
            const modal = document.getElementById('config-modal');
            const title = document.getElementById('modal-title');
            const body = document.getElementById('modal-body');
            
            title.textContent = `Configure ${currentOutput.name} - ${mode.toUpperCase()} Mode`;
            
            if (mode === 'periodic') {
                body.innerHTML = `
                    <div class="form-group">
                        <label>ON Duration (seconds)</label>
                        <input type="number" id="on-duration" value="${currentOutput.periodicConfig.onDuration}">
                    </div>
                    <div class="form-group">
                        <label>OFF Duration (seconds)</label>
                        <input type="number" id="off-duration" value="${currentOutput.periodicConfig.offDuration}">
                    </div>
                    <button onclick="savePeriodicConfig()" class="primary" style="width: 100%;">Save Configuration</button>
                    <button onclick="closeModal()" style="width: 100%; margin-top: 0.5rem;">Cancel</button>
                `;
            } else if (mode === 'scheduled') {
                body.innerHTML = `
                    <div class="form-group">
                        <label>Program Number (1-20)</label>
                        <input type="number" id="program-number" min="1" max="20" value="1">
                    </div>
                    <div class="form-group">
                        <label>ON Time</label>
                        <input type="time" id="on-time" value="08:00">
                    </div>
                    <div class="form-group">
                        <label>OFF Time</label>
                        <input type="time" id="off-time" value="18:00">
                    </div>
                    <button onclick="addScheduledProgram()" class="primary" style="width: 100%;">Add Program</button>
                    <div class="program-list" id="program-list">
                        ${currentOutput.scheduledPrograms.map(p => `
                            <div class="program-item">
                                <span>#${p.number}: ${p.onTime} - ${p.offTime}</span>
                                <button onclick="deleteProgram(${p.number})" class="danger">Delete</button>
                            </div>
                        `).join('')}
                    </div>
                    <button onclick="closeModal()" style="width: 100%; margin-top: 1rem;">Close</button>
                `;
            } else if (mode === 'sensor') {
                body.innerHTML = `
                    <div class="form-group">
                        <label>Sensor Type</label>
                        <select id="sensor-type">
                            <option value="temperature" ${currentOutput.sensorConfig.type === 'temperature' ? 'selected' : ''}>Temperature</option>
                            <option value="humidity" ${currentOutput.sensorConfig.type === 'humidity' ? 'selected' : ''}>Humidity</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Threshold Value</label>
                        <input type="number" id="threshold" value="${currentOutput.sensorConfig.threshold}">
                    </div>
                    <div class="form-group">
                        <label>Action when value < threshold</label>
                        <select id="action">
                            <option value="on" ${currentOutput.sensorConfig.action === 'on' ? 'selected' : ''}>Output ON</option>
                            <option value="off" ${currentOutput.sensorConfig.action === 'off' ? 'selected' : ''}>Output OFF</option>
                        </select>
                    </div>
                    <button onclick="saveSensorConfig()" class="primary" style="width: 100%;">Save Configuration</button>
                    <button onclick="closeModal()" style="width: 100%; margin-top: 0.5rem;">Cancel</button>
                `;
            }
            
            modal.classList.add('active');
        }
        
        function closeModal() {
            document.getElementById('config-modal').classList.remove('active');
        }
        
        async function savePeriodicConfig() {
            const onDuration = parseInt(document.getElementById('on-duration').value);
            const offDuration = parseInt(document.getElementById('off-duration').value);
            
            await fetch(`/api/outputs/${currentOutput.id}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    periodicConfig: {onDuration, offDuration}
                })
            });
            
            closeModal();
            fetchStatus();
        }
        
        async function saveSensorConfig() {
            const type = document.getElementById('sensor-type').value;
            const threshold = parseFloat(document.getElementById('threshold').value);
            const action = document.getElementById('action').value;
            
            await fetch(`/api/outputs/${currentOutput.id}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    sensorConfig: {type, threshold, action}
                })
            });
            
            closeModal();
            fetchStatus();
        }
        
        async function addScheduledProgram() {
            const number = parseInt(document.getElementById('program-number').value);
            const onTime = document.getElementById('on-time').value;
            const offTime = document.getElementById('off-time').value;
            
            if (currentOutput.scheduledPrograms.length >= 20) {
                alert('Maximum 20 programs allowed');
                return;
            }
            
            const programs = [...currentOutput.scheduledPrograms, {number, onTime, offTime}];
            
            await fetch(`/api/outputs/${currentOutput.id}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({scheduledPrograms: programs})
            });
            
            closeModal();
            openConfig(currentOutput.id, 'scheduled');
        }
        
        async function deleteProgram(programNumber) {
            const programs = currentOutput.scheduledPrograms.filter(p => p.number !== programNumber);
            
            await fetch(`/api/outputs/${currentOutput.id}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({scheduledPrograms: programs})
            });
            
            closeModal();
            openConfig(currentOutput.id, 'scheduled');
        }
        
        // Close modal on outside click
        document.getElementById('config-modal').addEventListener('click', (e) => {
            if (e.target.id === 'config-modal') closeModal();
        });
        
        // Initialize
        setInterval(updateTime, 1000);
        setInterval(fetchStatus, 1000);
        updateTime();
        fetchStatus();
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    print("=" * 60)
    print("🏭 Industrial Control System Dashboard")
    print("=" * 60)
    print("Starting Flask server...")
    print("Open your browser to: http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)