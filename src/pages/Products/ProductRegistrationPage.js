// src/pages/Products/ProductRegistrationPage.js
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import productService from '../../services/productService'; 
import PopupMessage from '../../components/Common/PopupMessage'; 
import useAuth from '../../hooks/useAuth'; 
import { ROLES } from '../../utils/constants'; 

// IMAGENS GHS
import explosivoImg from '../../assets/explosivo.png';
import gasPressaoImg from '../../assets/gas_pressao.png';
import inflamavelImg from '../../assets/inflamavel.png';
import corrosivoImg from '../../assets/corrosivo.png';
import irritacaoImg from '../../assets/Irritacao.png';
import cancerImg from '../../assets/cancer.png';
import MeioAmbienteImg from '../../assets/meio_ambiente.png';
import MorteImg from '../../assets/morte.png';
import OxidanteImg from '../../assets/oxidante.png';

// Upload form
import UploadForm from './UploadForm'; 

// Estilo
import '../../styles/productform.css'; 

// LISTAS DE SELEÇÃO
const empresas = [
  'AMARIS DO BRASIL ASSESSORIA EMPRESARIAL',
  'AMG - SOLUCOES INDUSTRIAIS',
  'BANCO ITAÚ S/A',
  'UNIPAC',
  'SODEXO'
  // ... restante da sua lista original
];

const local_de_armazenamento = [
  'Almoxarifado',
  'Armário corta fogo',
  'Casa de tintas',
  'Laboratórios',
  'Tancagem',
  'Toller'
  // ... restante da sua lista original
];

const ProductRegistrationPage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [message, setMessage] = useState('');
  const [showMessage, setShowMessage] = useState(false);
  const [loading, setLoading] = useState(false);

  // Estado do produto
  const [product, setProduct] = useState({
    qtade_maxima_armazenada: '',
    nome_do_produto: '',
    fornecedor: '',
    estado_fisico: '',
    local_de_armazenamento: '',
    empresa: '',
    perigos_fisicos: [],
    perigos_saude: [],
    perigos_meio_ambiente: [],
    palavra_de_perigo: '',
    categoria: '',
    pdf_url: '',
    pdf_s3_key: ''
  });

  // Substâncias
  const [substancias, setSubstancias] = useState([
    { nome: '', cas: '', concentracao: '' }
  ]);

  const [showUpload, setShowUpload] = useState(false);

  // Verificação de permissão
  useEffect(() => {
    if (!user || (user.role !== ROLES.ADMIN && user.role !== ROLES.ANALYST)) {
      setMessage('Você não tem permissão para cadastrar produtos.');
      setShowMessage(true);
      setTimeout(() => {
        navigate('/app/dashboard'); 
      }, 3000);  
    }
  }, [user, navigate]);

  // Handlers básicos
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setProduct({ ...product, [name]: value });
  };

  const handleCheckboxChange = (e) => {
    const { name, value, checked } = e.target;
    setProduct((prev) => ({
      ...prev,
      [name]: checked
        ? [...prev[name], value]
        : prev[name].filter((item) => item !== value),
    }));
  };

  const handleSubstanciaChange = (index, event) => {
    const { name, value } = event.target;
    const newSubs = [...substancias];
    newSubs[index][name] = value;
    setSubstancias(newSubs);
  };

  const handleAddSubstancia = () => {
    setSubstancias([...substancias, { nome: '', cas: '', concentracao: '' }]);
  };

  const handleRemoveSubstancia = (index) => {
    const newSubs = substancias.filter((_, i) => i !== index);
    setSubstancias(newSubs);
  };

  const handleFispqUploadComplete = (uploadedUrl, uploadedS3Key) => {
    setProduct(prev => ({
      ...prev,
      pdf_url: uploadedUrl,
      pdf_s3_key: uploadedS3Key
    }));
    setMessage('FDS anexado com sucesso! Salve o produto para confirmar.');
    setShowMessage(true);
    setShowUpload(false); 
  };

  // Envio do formulário
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    setShowMessage(false);

    // Permissão
    if (!user || (user.role !== ROLES.ADMIN && user.role !== ROLES.ANALYST)) {
      setMessage('Ação não permitida para o seu nível de acesso.');
      setShowMessage(true);
      setLoading(false);
      return;
    }

    // Validação alinhada ao backend
    if (
      !product.nome_do_produto.trim() ||
      !product.fornecedor.trim() ||
      !product.empresa.trim() ||
      !product.estado_fisico.trim() ||
      !product.local_de_armazenamento.trim()
    ) {
      setMessage('Preencha Nome, Fornecedor, Empresa, Estado Físico e Local de Armazenamento.');
      setShowMessage(true);
      setLoading(false);
      return;
    }

    const productDataToSend = {
      ...product,
      substancias: substancias.filter(
        s => s.nome.trim() || s.cas.trim() || s.concentracao.trim()
      ),
    };

    try {
      const response = await productService.createProduct(productDataToSend);
      setMessage(response.msg || `Produto ${response.product?.codigo} cadastrado com sucesso!`);
      setShowMessage(true);

      // Reset form
      setProduct({
        qtade_maxima_armazenada: '',
        nome_do_produto: '',
        fornecedor: '',
        estado_fisico: '',
        local_de_armazenamento: '',
        empresa: '',
        perigos_fisicos: [],
        perigos_saude: [],
        perigos_meio_ambiente: [],
        palavra_de_perigo: '',
        categoria: '',
        pdf_url: '',
        pdf_s3_key: ''
      });
      setSubstancias([{ nome: '', cas: '', concentracao: '' }]);

      console.log("✅ Produto criado:", response.product);

    } catch (error) {
      console.error('Erro ao adicionar produto:', error);
      const errorMessage = error.response?.data?.msg || 'Erro ao adicionar produto.';
      setMessage(errorMessage);
      setShowMessage(true);

      if (error.response && error.response.status === 403) {
        setTimeout(() => {
          navigate('/app/dashboard');
        }, 3000);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="product-form">
      <h2>Cadastro de Produtos</h2>
      <form onSubmit={handleSubmit}>
        {/* Card dados básicos */}
        <div className="card">
          <label>
            Quantidade Máx. Armazenada:
            <input type="text" name="qtade_maxima_armazenada" value={product.qtade_maxima_armazenada} onChange={handleInputChange}/>
          </label>
          <label>
            Nome do Produto:
            <input type="text" name="nome_do_produto" value={product.nome_do_produto} onChange={handleInputChange}/>
          </label>
          <label>
            Fornecedor:
            <input type="text" name="fornecedor" value={product.fornecedor} onChange={handleInputChange}/>
          </label>
          <label>
            Empresa:
            <select name="empresa" value={product.empresa} onChange={handleInputChange}>
              <option value="">Selecione...</option>
              {empresas.map((empresa, i) => <option key={i} value={empresa}>{empresa}</option>)}
            </select>
          </label>
          <label>
            Estado Físico:
            <select name="estado_fisico" value={product.estado_fisico} onChange={handleInputChange}>
              <option value="">Selecione...</option>
              <option value="Líquido">Líquido</option>
              <option value="Sólido">Sólido</option>
              <option value="Gasoso">Gasoso</option>
            </select>
          </label>
          <label>
            Local de Armazenamento:
            <select name="local_de_armazenamento" value={product.local_de_armazenamento} onChange={handleInputChange}>
              <option value="">Selecione...</option>
              {local_de_armazenamento.map((local, i) => <option key={i} value={local}>{local}</option>)}
            </select>
          </label>
        </div>

        {/* Substâncias */}
        <div className="card">
          <h2>Substâncias</h2>
          {substancias.map((s, i) => (
            <div key={i}>
              <input type="text" name="nome" placeholder="Substância" value={s.nome} onChange={(e)=>handleSubstanciaChange(i,e)}/>
              <input type="text" name="cas" placeholder="Número CAS" value={s.cas} onChange={(e)=>handleSubstanciaChange(i,e)}/>
              <input type="text" name="concentracao" placeholder="Concentração (%)" value={s.concentracao} onChange={(e)=>handleSubstanciaChange(i,e)}/>
              {substancias.length > 1 && <button type="button" onClick={()=>handleRemoveSubstancia(i)}>-</button>}
            </div>
          ))}
          <button type="button" onClick={handleAddSubstancia}>+</button>
        </div>

        
        <div className="card ghs-card">
          <h2>Classificação GHS</h2>
          <div className="ghs-container-horizontal">
            <div className="ghs-group-horizontal">
              <label>Perigos Físicos</label>
              <div className="image-checkbox-group">
                <label>
                  <input type="checkbox" name="perigos_fisicos" value="Explosivo" checked={product.perigos_fisicos.includes("Explosivo")} onChange={handleCheckboxChange}/>
                  <div className="image-with-text"><img src={explosivoImg} alt="Explosivo"/><span>Explosivo</span></div>
                </label>
                <label>
                  <input type="checkbox" name="perigos_fisicos" value="Inflamável" checked={product.perigos_fisicos.includes("Inflamável")} onChange={handleCheckboxChange}/>
                  <div className="image-with-text"><img src={inflamavelImg} alt="Inflamável"/><span>Inflamável</span></div>
                </label>
                <label>
                  <input type="checkbox" name="perigos_fisicos" value="Gás sob pressão" checked={product.perigos_fisicos.includes("Gás sob pressão")} onChange={handleCheckboxChange}/>
                  <div className="image-with-text"><img src={gasPressaoImg} alt="Gás sob pressão"/><span>Gás sob pressão</span></div>
                </label>
                <label>
                  <input type="checkbox" name="perigos_fisicos" value="Corrosivo" checked={product.perigos_fisicos.includes("Corrosivo")} onChange={handleCheckboxChange}/>
                  <div className="image-with-text"><img src={corrosivoImg} alt="Gás sob pressão"/><span>Corrosivo</span></div>
                </label>
                <label>
                  <input type="checkbox" name="perigos_fisicos" value="Oxidante" checked={product.perigos_fisicos.includes("Oxidante")} onChange={handleCheckboxChange}/>
                  <div className="image-with-text"><img src={OxidanteImg} alt="Gás sob pressão"/><span>Oxidante</span></div>
                </label>
              </div>
            </div>

            <div className="ghs-group-horizontal">
              <label>Perigos à Saúde</label>
              <div className="image-checkbox-group">
                <label>
                  <input type="checkbox" name="perigos_saude" value="Irritação da Pele" checked={product.perigos_saude.includes("Irritação da Pele")} onChange={handleCheckboxChange}/>
                  <div className="image-with-text"><img src={irritacaoImg} alt="Irritação"/><span>Irritação</span></div>
                </label>
                <label>
                  <input type="checkbox" name="perigos_saude" value="Toxicidade Aguda" checked={product.perigos_saude.includes("Toxicidade Aguda")} onChange={handleCheckboxChange}/>
                  <div className="image-with-text"><img src={MorteImg} alt="Toxicidade"/><span>Toxicidade</span></div>
                </label>
                <label>
                  <input type="checkbox" name="perigos_saude" value="Corrosão da Pele" checked={product.perigos_fisicos.includes("Corrosivo")} onChange={handleCheckboxChange}/>
                  <div className="image-with-text"><img src={corrosivoImg} alt="Gás sob pressão"/><span>Corrosivo</span></div>
                </label>
                <label>
                  <input type="checkbox" name="perigos_saude" value="Perigo por Respiração" checked={product.perigos_fisicos.includes("Perigo por Respiração")} onChange={handleCheckboxChange}/>
                  <div className="image-with-text"><img src={cancerImg} alt="Cancer"/><span>Cancer</span></div>
                </label>
              </div>
            </div>

            <div className="ghs-group-horizontal">
              <label>Perigos ao Meio Ambiente</label>
              <div className="image-checkbox-group">
                <label>
                  <input type="checkbox" name="perigos_meio_ambiente" value="Perigoso para o meio ambiente" checked={product.perigos_meio_ambiente.includes("Perigoso para o meio ambiente")} onChange={handleCheckboxChange}/>
                  <div className="image-with-text"><img src={MeioAmbienteImg} alt="Ambiente"/><span>Meio Ambiente</span></div>
                </label>
              </div>
            </div>
          </div>

          <div className="ghs-bottom-fields">
            <label>Palavra de Perigo
              <input type="text" name="palavra_de_perigo" value={product.palavra_de_perigo} onChange={handleInputChange}/>
            </label>
            <label>Categoria
              <input type="text" name="categoria" value={product.categoria} onChange={handleInputChange}/>
            </label>
          </div>
        </div>

        {/* Botões */}
        <div className="submit-button">
          <button type="button" className="fispq-button" onClick={()=>setShowUpload(true)}>Inserir FDS</button>
          <button type="submit" disabled={loading}>{loading ? 'Enviando...' : 'Enviar'}</button>
        </div>
      </form>

      {showUpload && (
        <UploadForm
          productNameForFispq={product.nome_do_produto}
          show={showUpload}
          onClose={()=>setShowUpload(false)}
          onUploadComplete={handleFispqUploadComplete}
        />
      )}

      {showMessage && (
        <PopupMessage 
          message={message} 
          onClose={()=>setShowMessage(false)} 
          type={message.includes('sucesso') ? 'success' : 'error'}
        />
      )}
    </div>
  );
};

export default ProductRegistrationPage;
