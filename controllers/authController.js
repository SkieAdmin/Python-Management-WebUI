const ADMIN_USERNAME = 'admin';
const ADMIN_PASSWORD = 'gocotano2025';

export const loginUser = (req, res) => {
  const { username, password } = req.body;

  if (username === ADMIN_USERNAME && password === ADMIN_PASSWORD) {
    req.session.user = { username };
    res.redirect('/');
  } else {
    res.render('login', { error: 'Invalid credentials' });
  }
};

export const logoutUser = (req, res) => {
  req.session.destroy();
  res.redirect('/auth/login');
};

export const authenticateUser = (req, res, next) => {
  if (req.session.user) {
    next();
  } else {
    res.redirect('/auth/login');
  }
};
