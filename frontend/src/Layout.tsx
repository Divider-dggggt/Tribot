import React from 'react';
import { Link, Outlet } from 'react-router-dom';
import Drawer from '@mui/material/Drawer';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';

const drawerWidth = 200;

function Layout() {
  return (
    <div style={{ display: 'flex' }}>
      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
          },
        }}
      >
        <List>
          <ListItem component={Link} to="/">
            <ListItemText primary="Dashboard" />
          </ListItem>
          <ListItem component={Link} to="/new-case">
            <ListItemText primary="New Case" />
          </ListItem>
        </List>
      </Drawer>

      <main>
        <Outlet /> 
      </main>
    </div>
  );
}

export default Layout;
