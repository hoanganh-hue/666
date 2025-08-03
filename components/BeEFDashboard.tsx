import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Modal } from 'antd';

interface Zombie {
    id: string;
    ip: string;
    browser: string;
    os: string;
    last_seen: string;
}

const BeEFDashboard: React.FC = () => {
    const [zombies, setZombies] = useState<Zombie[]>([]);
    const [selectedZombie, setSelectedZombie] = useState<string | null>(null);
    
    useEffect(() => {
        fetchZombies();
        const interval = setInterval(fetchZombies, 5000);
        return () => clearInterval(interval);
    }, []);
    
    const fetchZombies = async () => {
        const response = await fetch('/admin/beef/zombies');
        const data = await response.json();
        setZombies(data.zombies);
    };
    
    return (
        <Card title="BeEF Control Panel">
            <Table 
                dataSource={zombies} 
                columns={[
                    { title: 'Session', dataIndex: 'id' },
                    { title: 'IP Address', dataIndex: 'ip' },
                    { title: 'Browser', dataIndex: 'browser' },
                    { title: 'OS', dataIndex: 'os' },
                    { title: 'Last Seen', dataIndex: 'last_seen' },
                    {
                        title: 'Actions',
                        render: (_, record) => (
                            <Button onClick={() => setSelectedZombie(record.id)}>
                                Execute Module
                            </Button>
                        )
                    }
                ]}
            />
        </Card>
    );
};

export default BeEFDashboard;