import CircularProgress, {
  CircularProgressProps,
} from '@material-ui/core/es/CircularProgress';
import classNames from 'classnames';
import React from 'react';

import styles from './Loader.module.scss';

interface LoaderProps extends CircularProgressProps {
  className?: string;
}

const Loader: React.FC<LoaderProps> = ({ className, ...rest }) => (
  <div className={classNames(styles.loader, className)}>
    <CircularProgress {...rest} />
  </div>
);

export default Loader;
