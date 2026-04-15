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
import { clearAuthSession, getAccessToken, getDecodedToken } from './utils/auth';
import { dangerMenuItemHoverSx } from './utils/buttonStyles';
import { UserRole } from './types/user';
import { AuthTransitionOverlay } from './components/AuthTransitionOverlay';
import { ResetPasswordDialog } from './components/ResetPasswordDialog';

// Simple SVG Icons
const DashboardIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="7" height="7"></rect>
    <rect x="14" y="3" width="7" height="7"></rect>
    <rect x="14" y="14" width="7" height="7"></rect>
    <rect x="3" y="14" width="7" height="7"></rect>
  </svg>
);

const NewCaseIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
    <polyline points="14 2 14 8 20 8"></polyline>
    <line x1="12" y1="18" x2="12" y2="12"></line>
    <line x1="9" y1="15" x2="15" y2="15"></line>
  </svg>
);

const UserIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
    <circle cx="12" cy="7" r="4"></circle>
  </svg>
);

const LogoutIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: 8 }}>
    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
    <polyline points="16 17 21 12 16 7"></polyline>
    <line x1="21" y1="12" x2="9" y2="12"></line>
  </svg>
);

const ResetPasswordIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: 8 }}>
    <rect x="3" y="11" width="18" height="10" rx="2"></rect>
    <path d="M7 11V8a5 5 0 0 1 10 0v3"></path>
    <line x1="12" y1="16" x2="12" y2="16"></line>
  </svg>
);

const ChevronDownIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="6 9 12 15 18 9"></polyline>
  </svg>
);

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
              <UserIcon />
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
                <ChevronDownIcon />
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
              <ResetPasswordIcon />
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
              <LogoutIcon />
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
              color: '#7c3aed',
              fontWeight: 'bold',
              fontSize: '1.2rem',
              textDecoration: 'none',
              borderRadius: 1,
              '&:hover': {
                backgroundColor: 'transparent',
              },
            }}
          >
            <div style={{ width: 32, height: 32, backgroundColor: '#7c3aed', borderRadius: 8, marginRight: 8, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
              </svg>
            </div>
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
                  <DashboardIcon />
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
                  <NewCaseIcon />
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
