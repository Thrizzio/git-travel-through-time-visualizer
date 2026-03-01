export type TimelineSnapshot = {
  timestamp: number;

  commit_hash: string;
  author: string;
  email: string;
  message: string;
  files_changed: number;

  active_files: string[];
  file_sizes: Record<string, number>;
  churn: {
    lines_added: number;
    lines_deleted: number;
    total: number;
  };
  contributor_distribution: Record<string, number>;
  complexity: number;
};