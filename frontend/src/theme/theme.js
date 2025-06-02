import { createTheme } from '@mui/material/styles';
import { blue, lightBlue } from '@mui/material/colors';

const theme = createTheme({
  palette: {
    primary: {
      main: blue[500],
    },
    secondary: {
      main: lightBlue['A200'],
    },
  },
});

export default theme;
