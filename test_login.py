import httpx

# Step 1: Student login
r = httpx.post('http://localhost:8100/api/auth/login', json={'staff_id': '2024010001', 'password': '2024010001'})
print('Step 1 - Student Login:')
print(f'Status: {r.status_code}')
print(f'Response: {r.json()}')
print()

if r.status_code == 200:
    token = r.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # Step 2: Get user info
    r2 = httpx.get('http://localhost:8100/api/auth/me', headers=headers)
    print('Step 2 - Get User Info:')
    print(f'Status: {r2.status_code}')
    print(f'Response: {r2.json()}')
    print()
    
    # Step 3: Create conversation
    r3 = httpx.post('http://localhost:8100/api/conversations', headers=headers, json={'title': 'Test Conversation'})
    print('Step 3 - Create Conversation:')
    print(f'Status: {r3.status_code}')
    print(f'Response: {r3.json()}')
    print()
    
    if r3.status_code == 201:
        conv_id = r3.json()['id']
        
        # Step 4: Send message
        r4 = httpx.post(f'http://localhost:8100/api/conversations/{conv_id}/messages', 
                       headers=headers, json={'content': 'Hello, how to apply for campus card?'})
        print('Step 4 - Send Message:')
        print(f'Status: {r4.status_code}')
        print(f'Response: {r4.json()}')
        print()
        
        # Step 5: Get messages
        r5 = httpx.get(f'http://localhost:8100/api/conversations/{conv_id}/messages', headers=headers)
        print('Step 5 - Get Messages:')
        print(f'Status: {r5.status_code}')
        print(f'Message count: {len(r5.json()[" items\])}')
 print()
 
 # Step 6: Escalate
 r6 = httpx.post(f'http://localhost:8100/api/conversations/{conv_id}/escalate', headers=headers)
 print('Step 6 - Escalate:')
 print(f'Status: {r6.status_code}')
 print(f'Response: {r6.json()}')
 print()
