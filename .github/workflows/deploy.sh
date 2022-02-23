 #!/bin/sh
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -p $SSH_PORT -i ~/.ssh/id_rsa $SSH_USER@$HOST << EOF
    cd /var/www/html/api.paylend.africa
    git pull origin develop 
    npm i
    env HOME=/home/kifaru1/ pm2 restart 1
EOF