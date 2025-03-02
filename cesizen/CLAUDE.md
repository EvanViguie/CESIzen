# CESIzen Project Guidelines

## Documentation Commands
- Build docs: `bin/python -m mkdocs build`
- Serve docs locally: `bin/python -m mkdocs serve` (available at http://localhost:8000)
- Deploy docs to GitHub Pages: `bin/python -m mkdocs gh-deploy`

## Project Structure
- Documentation is written in Markdown in the `docs/` directory
- MkDocs with Material theme is used for documentation site generation
- The project appears to be focused on a mental health application called "CESIzen"

## Code Style
- Follow PEP 8 conventions for Python code
- Use 4 spaces for indentation (no tabs)
- Maximum line length of 88 characters
- Use descriptive variable and function names
- Include docstrings for functions and classes

## Error Handling
- Use try/except blocks to catch specific exceptions
- Log errors with appropriate context
- Provide helpful error messages to users

## Git Workflow
- Create feature branches for new work
- Write descriptive commit messages
- Open pull requests for code review before merging to main

## Documentation
- Keep documentation updated with code changes
- Use Markdown for all documentation files
- Include diagrams where appropriate (Mermaid is supported)

# Instructions for Generating the CESIZen Application

## Project Context
Develop a web and mobile application called "CESIZen" dedicated to stress management and mental health. This application targets the general public and follows a modular architecture.

## Technical Stack
- **Backend**: FastAPI for creating microservices
- **Frontend**: React for user interface
- **Database**: MongoDB
- **Caching**: Redis
- **Authentication**: JWT
- **Service Mesh**: Istio
- **API Gateway**: Envoy
- **GraphQL Layer**: Apollo
- **Containerization**: Docker
- **CI/CD**: GitHub Actions
- **Documentation**: MkDocs for technical documentation

## General Architecture
Implement a microservices architecture with the following components:
1. Envoy as API Gateway / Load Balancer
2. Istio for service mesh functionality
3. Authentication service
4. Business services (one per functional module)
5. Redis caching system
6. Messaging/events service
7. Apollo GraphQL server for frontend-backend communication

## Modules to Develop
1. **User Module** (mandatory):
    - API endpoints for account creation/management
    - JWT authentication with role management (visitor, user, admin)
    - Password reset functionality

2. **Information Module** (mandatory):
    - API for managing dynamic content
    - Admin interface for content modification

3. **Stress Diagnostic Module** (optional feature):
    - Implementation of Holmes and Rahe stress scale
    - Storage of diagnostic results
    - Visualization of results and recommendations

4. **Breathing Exercise Module** (optional feature):
    - Configurable API for cardiac coherence exercises
    - Interactive user interface with animation
    - Predefined modes: 748, 55, 46

## Security and Data Protection
- Implement HTTPS for all communications
- Password hashing with bcrypt
- GDPR compliance with explicit consent management
- Input validation and protection against injections
- Implementation of rate limiting and protection against DDOS attacks

## Frontend Structure (React)
- Component-based architecture
- Global state with Redux or Context API
- Protected routes according to user roles
- Multilingual support
- Responsive design with Mobile First approach
- Reusable UI components
- Apollo Client for GraphQL data fetching

## Backend Structure (FastAPI)
- Organization in microservices
- RESTful API with OpenAPI documentation
- GraphQL endpoints with Apollo
- Input data validation with Pydantic
- Unit tests with pytest
- Use of asyncio for asynchronous operations

## Database
- Document-based model with MongoDB
- Schema validation
- Indexing for performance optimization
- Aggregation pipelines for complex queries

## Deployment
- Containerization with Docker and Docker Compose
- Istio for service mesh management
- Configuration for local development and production
- CI/CD with GitHub Actions
- Automated testing before deployment

## Documentation
- Technical documentation with MkDocs
- API documentation with Swagger/OpenAPI
- Installation and deployment guides
- User documentation

## Specific Features to Implement
- Emotion tracking system with structured reference framework
- Interactive and timed breathing exercises
- Dynamic questionnaire for stress assessment
- Visualization graphs for emotion tracking

## Additional Security Considerations
- Regular security audits
- Security incident management
- Encryption of sensitive data
- Penetration testing

Start by establishing the basic project structure with Docker and Istio, then progressively develop each microservice starting with the authentication service, followed by the mandatory modules, and finally the optional features. Implement Redis for caching frequently accessed data and improve performance, and use Apollo GraphQL as the data layer between frontend and backend services.