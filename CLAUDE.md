# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a康养 (elderly care) project implementing AI-powered fall detection and alert system for elderly care centers. The system uses external AI modules attached to existing cameras to detect falls and send alerts through WeChat and a management dashboard.

## Project Architecture

The system consists of three main components:

1. **AI Detection Service** (Python-based)
   - Video stream processing from existing cameras via RTSP
   - Fall detection using computer vision (YOLO + PoseNet)
   - Real-time event processing and filtering

2. **Backend Management System** (Spring Boot)
   - RESTful APIs for alert management
   - Database operations for event logging
   - WeChat integration for notifications
   - System configuration management

3. **Frontend Dashboard** (Vue.js)
   - Real-time alert monitoring
   - Historical event queries
   - Camera status monitoring
   - System administration

## Technology Stack

- **Backend**: Spring Boot, MySQL/PostgreSQL, Redis
- **AI Processing**: Python, OpenCV, PyTorch/TensorFlow
- **Frontend**: Vue.js, Element UI
- **Message Queue**: RabbitMQ/Kafka for event processing
- **Deployment**: Docker containers on edge computing devices

## Development Commands

### Backend (Spring Boot)
```bash
# Build and run the application
./mvnw spring-boot:run

# Run tests
./mvnw test

# Build for production
./mvnw clean package

# Generate API documentation
./mvnw javadoc:javadoc
```

### AI Detection Service
```bash
# Install dependencies
pip install -r requirements.txt

# Run detection service
python main.py

# Run unit tests
pytest tests/

# Model training (if applicable)
python train_model.py
```

### Frontend
```bash
# Install dependencies
npm install

# Development server
npm run dev

# Build for production
npm run build

# Run tests
npm run test
```

## Core Business Logic

### Fall Detection Algorithm
- Uses pose estimation to track human body keypoints
- Analyzes rapid changes in body center of gravity
- Filters out normal sitting/lying movements
- Configurable sensitivity levels for different environments

### Alert System
- Immediate alerts for fall events (within 30 seconds)
- Escalation rules: normal events → duty staff; emergency → duty staff + supervisors
- WeChat notification format includes timestamp, location, event type, and action buttons

### Data Models
- **Camera**: Device management and stream configuration
- **Event**: Fall detection events with metadata
- **Alert**: Notification records and acknowledgment status
- **User**: Staff and administrator accounts

## Integration Points

### WeChat Integration
- Enterprise WeChat API for push notifications
- Message templates for different alert types
- Callback handling for alert acknowledgments

### HarmonyOS Ecosystem
- Reserved interfaces for future integration with HarmonyOS health devices
- Data format compatibility for multi-device health monitoring

## Deployment Considerations

### Edge Computing Setup
- AI inference runs on local edge devices (NVIDIA Jetson or industrial PCs)
- Minimal network dependency for core detection functionality
- Local storage with cloud backup for event data

### Performance Requirements
- Real-time video processing (30fps minimum)
- Alert delivery within 30 seconds of detection
- System uptime target: 99.5%
- False positive rate target: <5%

## Security and Privacy

- Video data processed locally, not transmitted to cloud
- Encrypted storage for event metadata
- RBAC (Role-Based Access Control) for management system
- Audit logging for all administrative actions

## Configuration Management

- Environment-specific configuration files
- Camera stream configuration via admin interface
- Detection sensitivity tuning per room/area
- Alert recipient management

This project serves as a pilot for elderly care technology integration, with emphasis on reliability, privacy, and ease of use for care facility staff.