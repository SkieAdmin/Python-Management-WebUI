import express from 'express';
import { loginUser, logoutUser } from '../controllers/authController.js';

const router = express.Router();

router.get('/login', (req, res) => {
  res.render('login', { error: null });
});

router.post('/login', loginUser);
router.get('/logout', logoutUser);

export default router;
