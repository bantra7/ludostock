import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/hooks/useAuth';

const Index = () => {
  const { user, loading, signOut } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading && !user) {
      navigate('/auth');
    }
  }, [user, loading, navigate]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <p className="text-xl text-muted-foreground">Chargement...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return null; // Will redirect to auth
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold">LudoStock</h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">
              Bonjour, {user.email}
            </span>
            <Button variant="outline" onClick={signOut}>
              Se deconnecter
            </Button>
          </div>
        </div>
      </header>
      
      <main className="container mx-auto px-4 py-8">
        <div className="text-center max-w-2xl mx-auto">
          <h2 className="text-4xl font-bold mb-4">Bienvenue sur LudoStock</h2>
          <p className="text-xl text-muted-foreground mb-8">
            Votre gestionnaire personnel de collection de jeux de societe. Organisez, partagez et retrouvez vos jeux plus facilement.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
            <div className="p-6 border rounded-lg">
              <h3 className="text-lg font-semibold mb-2">Ma collection</h3>
              <p className="text-muted-foreground">Gerez votre ludotheque simplement</p>
            </div>
            <div className="p-6 border rounded-lg">
              <h3 className="text-lg font-semibold mb-2">Listes de jeux</h3>
              <p className="text-muted-foreground">Creez et partagez des selections personnalisees</p>
            </div>
            <div className="p-6 border rounded-lg">
              <h3 className="text-lg font-semibold mb-2">Emplacements</h3>
              <p className="text-muted-foreground">Retrouvez ou chaque jeu est range</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Index;
