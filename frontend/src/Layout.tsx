import React, { useState } from 'react';
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';
import Drawer from '@mui/material/Drawer';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import CssBaseline from '@mui/material/CssBaseline';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import { API_BASE_URL } from './utils/constants';
import GroupIcon from '@mui/icons-material/Group';
import BarChartIcon from '@mui/icons-material/BarChart';
import DashboardOutlinedIcon from '@mui/icons-material/DashboardOutlined';
import NoteAddOutlinedIcon from '@mui/icons-material/NoteAddOutlined';
import PersonOutlineIcon from '@mui/icons-material/PersonOutline';
import LogoutOutlinedIcon from '@mui/icons-material/LogoutOutlined';
import LockResetOutlinedIcon from '@mui/icons-material/LockResetOutlined';
import ExpandMoreRoundedIcon from '@mui/icons-material/ExpandMoreRounded';
import { clearAuthSession, getAccessToken, getDecodedToken } from './utils/auth';
import { dangerMenuItemHoverSx } from './utils/buttonStyles';
import { UserRole } from './types/user';
import { AuthTransitionOverlay } from './components/AuthTransitionOverlay';
import { ResetPasswordDialog } from './components/ResetPasswordDialog';
import { BrandIcon } from './components/BrandIcon';

const drawerWidth = 240;
const LOGOUT_NAVIGATION_DELAY_MS = 450;
const ACCOUNT_MENU_HOVER_BG = '#f5f3ff';
const ACCOUNT_MENU_HOVER_TEXT = '#6d28d9';
const ACCOUNT_TRIGGER_BORDER = '#e5e7eb';
const ACCOUNT_TRIGGER_ACTIVE_BORDER = '#c4b5fd';
const ACCOUNT_TRIGGER_HOVER_BORDER = '#d8b4fe';
const ACCOUNT_TRIGGER_HOVER_BG = '#faf5ff';
const ROLE_BADGE_STYLES: Record<UserRole, { backgroundColor: string; color: string }> = {
  [UserRole.Admin]: {
    backgroundColor: '#e9e1ff',
    color: '#5b2ecb',
  },
  [UserRole.Clinician]: {
    backgroundColor: '#d3efdf',
    color: '#166534',
  },
  [UserRole.Researcher]: {
    backgroundColor: '#e0f2fe',
    color: '#0c4a6e',
  },
};

function Layout() {
  const location = useLocation();
  const navigate = useNavigate();
  const [isLoggingOut, setIsLoggingOut] = useState<boolean>(false);
  const [isResetPasswordOpen, setIsResetPasswordOpen] = useState<boolean>(false);
  const [accountMenuAnchor, setAccountMenuAnchor] = useState<HTMLElement | null>(null);
  const decodedToken = getDecodedToken();
  const signedInEmail = localStorage.getItem('user_email');
  const userRole = decodedToken?.role;
  const userId = decodedToken?.user_id ?? null;
  const roleBadgeStyle = userRole ? ROLE_BADGE_STYLES[userRole] : null;
  const isAccountMenuOpen = accountMenuAnchor != null;

  const handleOpenAccountMenu = (event: React.MouseEvent<HTMLElement>): void => {
    setAccountMenuAnchor(event.currentTarget);
  };

  const handleCloseAccountMenu = (): void => {
    setAccountMenuAnchor(null);
  };

  const handleLogout = async () => {
    if (isLoggingOut) {
      return;
    }

    setIsLoggingOut(true);
    const accessToken = getAccessToken();

    try {
      if (accessToken) {
        await fetch(`${API_BASE_URL}/logout`, {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        });
      }
    } catch {
      // Ignore network errors and clear local session anyway.
    } finally {
      await new Promise<void>((resolve) => {
        window.setTimeout(resolve, LOGOUT_NAVIGATION_DELAY_MS);
      });
      clearAuthSession();
      navigate('/login', { replace: true });
    }
  };

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      
      {/* Top App Bar */}
      <AppBar
        position="fixed"
        sx={{
          width: `calc(100% - ${drawerWidth}px)`,
          ml: `${drawerWidth}px`,
          bgcolor: 'white',
          color: 'black',
          boxShadow: 'none',
          borderBottom: '1px solid #e0e0e0',
          zIndex: (theme) => theme.zIndex.drawer + 1
        }}
      >
        <Toolbar sx={{ justifyContent: 'flex-end' }}>
          <Button
            color="inherit"
            sx={{
              textTransform: 'none',
              px: 1.2,
              py: 0.55,
              borderRadius: 999,
              minHeight: 44,
              border: '1px solid',
              borderColor: isAccountMenuOpen ? ACCOUNT_TRIGGER_ACTIVE_BORDER : ACCOUNT_TRIGGER_BORDER,
              backgroundColor: isAccountMenuOpen ? ACCOUNT_TRIGGER_HOVER_BG : '#fff',
              transition: 'all 180ms ease',
              '&:hover': {
                borderColor: ACCOUNT_TRIGGER_HOVER_BORDER,
                backgroundColor: ACCOUNT_TRIGGER_HOVER_BG,
              },
            }}
            onClick={handleOpenAccountMenu}
            aria-controls={isAccountMenuOpen ? 'account-menu' : undefined}
            aria-expanded={isAccountMenuOpen ? 'true' : undefined}
            aria-haspopup="true"
          >
            <Box
              component="span"
              sx={{
                width: 30,
                height: 30,
                borderRadius: '50%',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                mr: 1,
                color: ACCOUNT_MENU_HOVER_TEXT,
                backgroundColor: ACCOUNT_MENU_HOVER_BG,
              }}
            >
              <PersonOutlineIcon sx={{ fontSize: 18 }} />
            </Box>
            <Box component="span" sx={{ display: 'inline-flex', alignItems: 'center', gap: 1.5 }}>
              <Box
                component="span"
                sx={{
                  maxWidth: { xs: 140, sm: 190, md: 230 },
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  color: '#374151',
                  fontWeight: 500,
                }}
              >
                {signedInEmail ?? 'Signed In User'}
              </Box>
              {userRole && roleBadgeStyle ? (
                <Box
                  component="span"
                  sx={{
                    px: 1.5,
                    py: 0.35,
                    borderRadius: 999,
                    fontSize: '0.9rem',
                    fontWeight: 700,
                    lineHeight: 1,
                    backgroundColor: roleBadgeStyle.backgroundColor,
                    color: roleBadgeStyle.color,
                  }}
                >
                  {userRole}
                </Box>
              ) : null}
              <Box
                component="span"
                sx={{
                  color: isAccountMenuOpen ? ACCOUNT_MENU_HOVER_TEXT : '#6b7280',
                  display: 'inline-flex',
                  alignItems: 'center',
                  transition: 'transform 150ms ease, color 150ms ease',
                  transform: isAccountMenuOpen ? 'rotate(180deg)' : 'rotate(0deg)',
                }}
              >
                <ExpandMoreRoundedIcon sx={{ fontSize: 18 }} />
              </Box>
            </Box>
          </Button>
          <Menu
            id="account-menu"
            anchorEl={accountMenuAnchor}
            open={isAccountMenuOpen}
            onClose={handleCloseAccountMenu}
            transformOrigin={{ horizontal: 'right', vertical: 'top' }}
            anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
            slotProps={{
              paper: {
                sx: {
                  mt: 1,
                  minWidth: 220,
                  p: 0.75,
                  borderRadius: 2.5,
                  border: '1px solid #ede9fe',
                  boxShadow: '0 16px 36px rgba(15, 23, 42, 0.14)',
                },
              },
            }}
          >
            <MenuItem
              onClick={() => {
                handleCloseAccountMenu();
                setIsResetPasswordOpen(true);
              }}
              disabled={isLoggingOut}
              sx={{
                py: 1.1,
                px: 1.4,
                borderRadius: 1.5,
                fontWeight: 500,
                color: '#374151',
                '&:hover': {
                  color: ACCOUNT_MENU_HOVER_TEXT,
                  backgroundColor: ACCOUNT_MENU_HOVER_BG,
                },
              }}
            >
              <LockResetOutlinedIcon sx={{ mr: 1, fontSize: 20 }} />
              Reset Password
            </MenuItem>
            <MenuItem
              onClick={() => {
                handleCloseAccountMenu();
                void handleLogout();
              }}
              disabled={isLoggingOut}
              sx={{
                py: 1.1,
                px: 1.4,
                borderRadius: 1.5,
                fontWeight: 500,
                color: '#374151',
                ...dangerMenuItemHoverSx,
              }}
            >
              <LogoutOutlinedIcon sx={{ mr: 1, fontSize: 20 }} />
              {isLoggingOut ? 'Logging out...' : 'Logout'}
            </MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>

      {/* Sidebar Drawer */}
      <Drawer
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
            borderRight: '1px solid #e0e0e0',
          },
        }}
        variant="permanent"
        anchor="left"
      >
        <Toolbar sx={{ display: 'flex', alignItems: 'center', px: 2 }}>
          {/* Logo Placeholder */}
          <Box
            component={Link}
            to="/dashboard"
            sx={{
              display: 'flex',
              alignItems: 'center',
              color: '#111827',
              fontWeight: 700,
              letterSpacing: 0.4,
              fontSize: '1.1rem',
              textDecoration: 'none',
              borderRadius: 1,
              '&:hover': {
                backgroundColor: 'transparent',
              },
            }}
          >
            <Box sx={{ mr: 1, display: 'inline-flex' }}>
              <BrandIcon size={32} iconSize={18} />
            </Box>
            TRIBOT
          </Box>
        </Toolbar>
        <Box sx={{ overflow: 'auto', mt: 2 }}>
          <List>
            <ListItem disablePadding>
              <ListItemButton 
                component={Link} 
                to="/dashboard"
                selected={location.pathname === '/dashboard'}
                sx={{
                  mx: 1,
                  borderRadius: 2,
                }}
              >
                <ListItemIcon sx={{ minWidth: 40 }}>
                  <DashboardOutlinedIcon />
                </ListItemIcon>
                <ListItemText primary="Dashboard" primaryTypographyProps={{ fontWeight: location.pathname === '/dashboard' ? 'bold' : 'medium' }} />
              </ListItemButton>
            </ListItem>
            
            {userRole === UserRole.Clinician && <ListItem disablePadding sx={{ mt: 1 }}>
              <ListItemButton 
                component={Link} 
                to="/new-case"
                selected={location.pathname === '/new-case'}
                sx={{
                  mx: 1,
                  borderRadius: 2,
                }}
              >
                <ListItemIcon sx={{ minWidth: 40 }}>
                  <NoteAddOutlinedIcon />
                </ListItemIcon>
                <ListItemText primary="New Case" primaryTypographyProps={{ fontWeight: location.pathname === '/new-case' ? 'bold' : 'medium' }} />
              </ListItemButton>
            </ListItem>}

            {userRole === UserRole.Admin && <ListItem disablePadding sx={{ mt: 1 }}>
              <ListItemButton 
                component={Link} 
                to="/users"
                selected={location.pathname === '/users'}
                sx={{
                  mx: 1,
                  borderRadius: 2,
                }}
              >
                <ListItemIcon sx={{ minWidth: 40 }}>
                  <GroupIcon />
                </ListItemIcon>
                <ListItemText primary="Users" primaryTypographyProps={{ fontWeight: location.pathname === '/users' ? 'bold' : 'medium' }} />
              </ListItemButton>
            </ListItem>}

            {userRole === UserRole.Researcher && <ListItem disablePadding sx={{ mt: 1 }}>
              <ListItemButton 
                component={Link} 
                to="/metrics"
                selected={location.pathname === '/metrics'}
                sx={{
                  mx: 1,
                  borderRadius: 2,
                }}
              >
                <ListItemIcon sx={{ minWidth: 40 }}>
                  <BarChartIcon />
                </ListItemIcon>
                <ListItemText primary="Metrics" primaryTypographyProps={{ fontWeight: location.pathname === '/metrics' ? 'bold' : 'medium' }} />
              </ListItemButton>
            </ListItem>}
          </List>
        </Box>
      </Drawer>

      {/* Main Content */}
      <Box
        component="main"
        sx={{ flexGrow: 1, bgcolor: '#f9fafb', p: 3, minHeight: '100vh' }}
      >
        <Toolbar /> {/* Spacer for fixed AppBar */}
        <Outlet />
      </Box>
      <AuthTransitionOverlay
        open={isLoggingOut}
        variant="logout"
        title="Signing out"
        subtitle="Securing your session..."
      />
      <ResetPasswordDialog
        open={isResetPasswordOpen}
        onClose={() => setIsResetPasswordOpen(false)}
        signedInEmail={signedInEmail}
        userId={userId}
      />
    </Box>
  );
}

export default Layout;
