import React from 'react';
import { Navigate } from 'react-router-dom';
import AlumniRegisterPage from '../alumni/AlumniRegisterPage';

/*
// ===== OLD STUDENT REGISTRATION FORM (DISABLED & PRESERVED) =====
// Student registration is permanently disabled from the active public user flow.
// The code is preserved below for reference and backup.
//
// const OldStudentRegisterForm = () => {
//   return <div>Old Student Registration Form Disabled</div>;
// };
// ===== END OLD STUDENT REGISTRATION FORM =====
*/

const RegisterPage = () => {
  // Directly render AlumniRegisterPage or navigate to /alumni/register
  return <AlumniRegisterPage />;
};

export default RegisterPage;
