import re

with open('plans/api_expose.md', 'r') as f:
    content = f.read()

content = content.replace('- [ ] API routes are protected by the `API_KEY`.', '- [x] API routes are protected by the `API_KEY`.')
content = content.replace('- [ ] Third-party requests can successfully start a task and receive an `execution_id`.', '- [x] Third-party requests can successfully start a task and receive an `execution_id`.')
content = content.replace('- [ ] Follow-up messages correctly resume the conversation in the same environment.', '- [x] Follow-up messages correctly resume the conversation in the same environment.')
content = content.replace('- [ ] Inactive threads are automatically closed after the defined timeout.', '- [x] Inactive threads are automatically closed after the defined timeout.')
content = content.replace('- [ ] Web UI functionality remains intact and bug-free.', '- [x] Web UI functionality remains intact and bug-free.')
content = content.replace('- [ ] Documentation is updated and accurate.', '- [x] Documentation is updated and accurate.')

with open('plans/api_expose.md', 'w') as f:
    f.write(content)

